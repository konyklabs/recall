# recall

One Claude Code auto-memory directory for every repository on a machine, kept in git, readable
as an Obsidian vault.

**The problem.** Working across many repositories in a day, each with its own `CLAUDE.md`, you
restate the same answers again and again. Claude Code's auto memory is per repository by default,
so what a session learned in one checkout is unknown in the next.

**The mechanism.** Claude Code reads the `autoMemoryDirectory` setting from user scope. One
absolute path there routes every repository without its own override to the same directory. The
directory's `MEMORY.md` index (first 200 lines or 25 KB) loads at every session start; topic
files load on demand. Memory files are one fact per file with frontmatter and `[[wikilinks]]`,
which is exactly the shape a markdown vault renders as a graph with backlinks and search.

Verified against the Claude Code docs on 2026-10-19: https://code.claude.com/docs/en/memory

## What is in the box

- `bin/recall`: a stdlib Python script, no dependencies.
  - `recall init --dir DIR`: sets `autoMemoryDirectory` in user settings (merging the one key,
    touching nothing else), makes `DIR` a git repository with an index and an ignore file.
  - `recall migrate --dir DIR [--dry-run]`: copies every per-project memory the machine already
    holds (`~/.claude/projects/*/memory/`) into `DIR`. Originals are never touched. Same name,
    same bytes: kept once. Same name, different content: the second is renamed
    `<project>--<name>.md` and its own links rewritten. A renamed copy that was edited since:
    left alone and reported as a conflict. Each source's index lines land under a
    `## From <project>` heading; a memory without an index line gets one from its frontmatter.
    A directory already relocated by a project-scope setting (a symlink) is skipped and named.
  - `recall check [--dir DIR]`: frontmatter present with `name` and `description`, every file
    indexed and every index line resolving, the index under the start-up load limit. It reports;
    it never rewrites a memory to satisfy itself.
  - `recall status`: where memory resolves to, counts, git state, how many per-project
    directories still wait to be gathered.
- `docs/setup-prompt.md`: the paste-in prompt. A Claude Code session on a fresh machine runs the
  whole setup from it, dry run first.
- `scripts/check.sh`: the repository's own check (tests, compile, actionlint when present).

## Use

```
git clone https://github.com/konyklabs/recall ~/dev/recall
~/dev/recall/bin/recall init --dir ~/.claude/memory
~/dev/recall/bin/recall migrate --dry-run        # read the report
~/dev/recall/bin/recall migrate
~/dev/recall/bin/recall check
cd ~/.claude/memory && git add -A && git commit -m "Gather the machine's auto memory"
```

A new Claude Code session in any repository then carries the shared index. A repository that sets
its own `autoMemoryDirectory` in `.claude/settings.json` keeps it: project scope overrides user
scope, which is how a team-versioned memory and a personal one coexist.

Optional, after the above:

- **Obsidian:** open `~/.claude/memory` as a vault ("Open folder as vault"). Graph view shows the
  `[[wikilinks]]`, backlinks show what cites a fact, search is full text. `.obsidian/` is ignored
  by the directory's `.gitignore` already.
- **Capture:** the `supervisor` plugin from `konyklabs/claude-plugins` queues corrections and
  "from now on" rules you type, and `/supervisor:reflect` turns the ones you accept into memory
  files in this directory.
- **A private remote:** `git remote add origin <your private repository>` in the memory directory
  carries it to a second machine. The kit never adds a remote.

## What it is not

Per-person memory, not a team knowledge base. Nothing here indexes code, tickets or documents;
it only stops one person's sessions from forgetting what they were told.

## Rules of the repository

Branch per change, conventional-commit pull-request titles with a task reference, squash
merges, `scripts/check.sh` green with its output in the pull-request body. The org's CI callers
(title lint, proprietary-terms scan, on-demand review) run on pull requests.
