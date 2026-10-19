"""Tests for bin/recall. Run: python3 -m unittest discover -s tests -v"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from importlib.machinery import SourceFileLoader
loader = SourceFileLoader("recall", str(ROOT / "bin" / "recall"))
spec = importlib.util.spec_from_loader("recall", loader)
recall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recall)


def mem(name, desc, body="", type_="project"):
    return f"---\nname: {name}\ndescription: {desc}\nmetadata:\n  type: {type_}\n---\n\n{body}\n"


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = self.tmp / "cfg"
        self.target = self.tmp / "shared"
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.cfg)
        home_key = "-" + str(Path.home()).strip("/").replace("/", "-")
        self.a = self.cfg / "projects" / f"{home_key}-dev-alpha" / "memory"
        self.b = self.cfg / "projects" / f"{home_key}-dev-beta" / "memory"
        for d in (self.a, self.b):
            d.mkdir(parents=True)
        (self.a / "shared-fact.md").write_text(mem("shared-fact", "alpha's fact", "alpha body, see [[alpha-only]]"))
        (self.a / "alpha-only.md").write_text(mem("alpha-only", "only alpha"))
        (self.a / "same.md").write_text(mem("same", "identical in both"))
        (self.a / "unindexed.md").write_text(mem("unindexed", "no index line", type_="feedback"))
        (self.a / "MEMORY.md").write_text(
            "# Memory index\n\n- [Shared](shared-fact.md) — alpha's fact\n- [Alpha only](alpha-only.md) — only alpha\n"
            "- [Same](same.md) — identical\n- [Gone](gone.md) — file deleted long ago\n")
        (self.b / "shared-fact.md").write_text(mem("shared-fact", "beta's different fact", "beta body, links [[shared-fact]]"))
        (self.b / "same.md").write_text(mem("same", "identical in both"))
        (self.b / "MEMORY.md").write_text("# Memory index\n\n- [Shared](shared-fact.md) — beta's fact\n- [Same](same.md) — identical\n")

    def run_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = recall.main(list(argv))
        return code, out.getvalue()


class MigrateTests(Fixture):
    def test_dry_run_writes_nothing(self):
        code, out = self.run_cli("migrate", "--dir", str(self.target), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn("rename shared-fact.md -> dev-beta--shared-fact.md", out)
        self.assertIn("dangling (not carried): - [Gone](gone.md)", out)
        self.assertFalse(self.target.exists() and any(self.target.iterdir()))

    def test_migrate_copies_renames_and_indexes(self):
        code, out = self.run_cli("migrate", "--dir", str(self.target))
        self.assertEqual(code, 0, out)
        names = sorted(p.name for p in self.target.glob("*.md"))
        self.assertEqual(names, ["MEMORY.md", "alpha-only.md", "dev-beta--shared-fact.md", "same.md", "shared-fact.md", "unindexed.md"])
        # the renamed file's own wikilink and index line were rewritten; the source was not touched
        self.assertIn("[[dev-beta--shared-fact]]", (self.target / "dev-beta--shared-fact.md").read_text())
        self.assertIn("[[shared-fact]]", (self.b / "shared-fact.md").read_text())
        idx = (self.target / "MEMORY.md").read_text()
        self.assertIn("## From dev-alpha", idx)
        self.assertIn("## From dev-beta", idx)
        self.assertIn("(dev-beta--shared-fact.md)", idx)
        self.assertIn("- [unindexed](unindexed.md) — no index line", idx)
        self.assertNotIn("gone.md", idx)
        # alpha's own link to a file that only alpha has stays as it was
        self.assertIn("[[alpha-only]]", (self.target / "shared-fact.md").read_text())
        # sources byte-identical to before
        self.assertEqual(sorted(p.name for p in self.a.glob("*.md")), ["MEMORY.md", "alpha-only.md", "same.md", "shared-fact.md", "unindexed.md"])

    def test_second_run_is_idempotent(self):
        self.run_cli("migrate", "--dir", str(self.target))
        before = {p.name: p.read_bytes() for p in self.target.glob("*.md")}
        code, out = self.run_cli("migrate", "--dir", str(self.target))
        self.assertEqual(code, 0)
        after = {p.name: p.read_bytes() for p in self.target.glob("*.md")}
        self.assertEqual(before, after)
        self.assertIn("written: 0 files, 0 index sections", out)
        self.assertIn("identical 6", out.split("total:")[1])

    def test_conflict_is_left_alone_and_reported(self):
        self.run_cli("migrate", "--dir", str(self.target))
        (self.target / "dev-beta--shared-fact.md").write_text(mem("shared-fact", "edited after migration by reflect"))
        code, out = self.run_cli("migrate", "--dir", str(self.target))
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT shared-fact.md: dev-beta--shared-fact.md already exists", out)
        self.assertIn("edited after migration", (self.target / "dev-beta--shared-fact.md").read_text())

    def test_check_passes_after_migrate_and_fails_on_broken_memory(self):
        self.run_cli("migrate", "--dir", str(self.target))
        code, out = self.run_cli("check", "--dir", str(self.target))
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors", out)
        (self.target / "bare.md").write_text("no frontmatter at all\n")
        code, out = self.run_cli("check", "--dir", str(self.target))
        self.assertEqual(code, 1)
        self.assertIn("bare.md: no frontmatter", out)
        self.assertIn("bare.md: not in MEMORY.md", out)

    def test_check_flags_index_over_limit_and_dangling_index_link(self):
        self.target.mkdir()
        (self.target / "a.md").write_text(mem("a", "x"))
        lines = ["# Memory index", "", "- [a](a.md) — x", "- [b](b.md) — missing"] + [f"- [a](a.md) — pad {i}" for i in range(recall.INDEX_LINE_LIMIT)]
        (self.target / "MEMORY.md").write_text("\n".join(lines) + "\n")
        code, out = self.run_cli("check", "--dir", str(self.target))
        self.assertEqual(code, 1)
        self.assertIn("points at missing b.md", out)
        self.assertIn("exceeds the start-up load", out)


class SourceRulesTests(Fixture):
    def test_symlinked_source_is_skipped_and_prose_index_reported(self):
        real = self.tmp / "elsewhere"; real.mkdir()
        (real / "x.md").write_text(mem("x", "relocated"))
        link = self.cfg / "projects" / "-Users-someone-dev-moved" / "memory"
        link.parent.mkdir(parents=True); link.symlink_to(real)
        (self.b / "MEMORY.md").write_text("# Notes\n\n## Overview\n- free prose, no link\n- [Same](same.md) — identical\n")
        code, out = self.run_cli("migrate", "--dir", str(self.target), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped (already relocated", out)
        self.assertIn(str(real), out)
        self.assertIn("1 prose line(s) in the source index", out)
        self.assertNotIn("[dev-moved]", out)


class InitAndStatusTests(Fixture):
    def test_init_merges_one_key_and_keeps_the_rest(self):
        self.cfg.mkdir(parents=True, exist_ok=True)
        (self.cfg / "settings.json").write_text(json.dumps({"model": "opus", "hooks": {"SessionStart": []}}))
        code, out = self.run_cli("init", "--dir", str(self.target))
        self.assertEqual(code, 0, out)
        s = json.loads((self.cfg / "settings.json").read_text())
        self.assertEqual(s["autoMemoryDirectory"], str(self.target.resolve()))
        self.assertEqual(s["model"], "opus")
        self.assertEqual(s["hooks"], {"SessionStart": []})
        self.assertTrue((self.target / ".git").is_dir())
        self.assertTrue((self.target / "MEMORY.md").exists())
        self.assertIn(".obsidian/", (self.target / ".gitignore").read_text())
        code, out = self.run_cli("init", "--dir", str(self.target))
        self.assertIn("already", out)

    def test_status_reports_resolution_and_sources(self):
        self.run_cli("init", "--dir", str(self.target))
        code, out = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertIn(str(self.target.resolve()), out)
        self.assertIn("per-project   2 directories", out)

    def test_cli_entry_point_runs(self):
        r = subprocess.run([sys.executable, str(ROOT / "bin" / "recall"), "status", "--dir", str(self.target)],
                           capture_output=True, text=True, env={**os.environ, "CLAUDE_CONFIG_DIR": str(self.cfg)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("missing", r.stdout)


if __name__ == "__main__":
    unittest.main()
