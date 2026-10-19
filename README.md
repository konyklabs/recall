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
which Obsidian-style markdown vaults render as a graph with backlinks and search.

The behaviour described here was checked against that docs page on 2026-10-19; the docs may have changed since: https://code.claude.com/docs/en/memory

You need Claude Code itself (a third-party tool; checked with version 2.1.303), `git` and Python 3.9 or newer.

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
    directories exist (the dry run says what in them is new).
  - `recall mount <repo>/.claude/memory`: a repository that keeps its own versioned memory
    (a project-scope `autoMemoryDirectory`) is invisible to a session started anywhere else,
    including a parent folder above several repositories. `mount` makes its index load in every
    session on the machine: an `@import` by absolute path inside a block the kit owns in the
    user-level `CLAUDE.md` (user-scope imports load without a dialog, from any directory), a
    symlink under `<DIR>/mounts/` so the vault draws one graph, and a sentence telling sessions
    that facts about that repository are written to its directory. `recall unmount <name>`
    reverses it. `status` prints what the mounts cost per session; `check` covers them.
    Observed once on 2026-10-19, in a manual run that is not part of the test suite: a memory-only
    fact of a mounted repository was answered from a session started in the parent folder and
    from an unrelated repository.
- `docs/setup-prompt.md`: the paste-in prompt. A Claude Code session on a fresh machine runs the
  whole setup from it, dry run first.
- `scripts/check.sh`: the repository's own check (tests, compile, actionlint when present).

## Use

```
git clone https://github.com/konyklabs/recall ~/dev/recall
mkdir -p ~/.local/bin && ln -sf ~/dev/recall/bin/recall ~/.local/bin/recall   # optional, if ~/.local/bin is on PATH
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
- **Capture:** a separate project, github.com/konyklabs/claude-plugins (not part of this
  repository), has a Claude Code plugin that queues the corrections you type and writes the ones
  you accept as memory files here. It runs hooks in every session; read its README first. The kit
  works without it.
- **A private remote:** `git remote add origin <your private repository>` in the memory directory
  carries it to a second machine. The kit never adds a remote. Memory written while working in
  any repository is stored in this directory, so never push it to a public remote, and check your
  employer's policy before gathering memory from work repositories.

## Sitting above the repositories

A session loads the memory of the directory it starts in and no other, and a repository's
`.claude/settings.json` is never inherited by a parent. Rules are fine: a nested `CLAUDE.md`
loads on demand once the session touches a file in it. Memory is not, and a pointer injected at
start-up was seen but not followed in one manual trial. `recall mount` is the answer: the repository's
index is imported into every session. The cost is that every mount loads at every start, so
mount what is in play this month; `recall status` shows the total. Writes from a parent-rooted
session still go to the shared directory; the block's sentence is the mitigation, not a redirect.

## What it is not

Per-person memory, not a team knowledge base. Nothing here indexes code, tickets or documents;
it only stops one person's sessions from forgetting what they were told.

## Rules of the repository

Branch per change, conventional-commit pull-request titles with a task reference, squash
merges, `scripts/check.sh` green with its output in the pull-request body. CI checks pull-request
titles and scans for disallowed terms; reviews run on request. Those workflows call reusable
workflows in the konyklabs organisation, so they do not run on forks; `scripts/check.sh` is the
whole check and runs anywhere.

## License

MIT. See `LICENSE`.
