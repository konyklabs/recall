# Setup prompt

Paste the block below as the first message of a Claude Code session on the machine to set up.
Start the session in your home directory or above your checkouts, not inside a repository that
sets its own memory directory. The session needs `git` and `python3` (3.9 or newer).

What it changes, all under your home directory: one key in `~/.claude/settings.json`; a new
directory `~/.claude/memory` with a git repository in it; a checkout of this kit in `~/dev/recall`;
and, only in step 9 and only for repositories you confirm, a marked block in `~/.claude/CLAUDE.md`
plus symlinks inside the memory directory. Nothing is deleted from any repository or from the
original per-project memory. Network: `git clone` and `git pull` from github.com, and two short
`claude -p` model calls in step 7. Replace the directory path if you want the memory elsewhere.
Check your employer's policy before gathering memory written while working in work repositories;
that memory is personal notes about those repositories and lives in this one directory.

````
Set up a shared Claude Code memory directory on this machine with the recall kit. Do these steps
in order, show the command and its output for each, and stop at any step whose output you cannot
show. Run nothing that is not listed here. The only network calls are the git clone or pull in
step 1 and the two model calls in step 7. Do not install anything.

1. Clone the kit: `git clone https://github.com/konyklabs/recall ~/dev/recall` (if the directory
   exists, `git -C ~/dev/recall pull --ff-only` instead). Run `~/dev/recall/scripts/check.sh` and
   paste the last line.
2. Show me the current state: `~/dev/recall/bin/recall status`.
3. Initialise: `~/dev/recall/bin/recall init --dir ~/.claude/memory`. This merges one key,
   autoMemoryDirectory, into my user settings and leaves every other key as it was; confirm that
   by running `~/dev/recall/bin/recall status` before and after, and by showing the key list of
   the settings file before and after with
   `python3 -c 'import json,os; p=os.path.join(os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude")), "settings.json"); print(sorted(json.load(open(p))) if os.path.exists(p) else "no settings.json yet")'`.
4. Dry run the migration: `~/dev/recall/bin/recall migrate --dry-run`. Paste the whole report.
   Point out any line that says rename, CONFLICT, dangling or skipped, and what it means.
5. Migrate for real: `~/dev/recall/bin/recall migrate`. Then `~/dev/recall/bin/recall check` and
   paste its last line. Errors are findings for me, not for you to fix by editing memory files.
6. Commit the new memory directory (it was created in step 3, so `add -A` there touches nothing
   else): `git -C ~/.claude/memory add -A && git -C ~/.claude/memory commit -m "Gather this machine's auto memory"`.
   Do not add a remote.
7. Prove alignment: run `claude -p --model haiku "Without using any tool: what absolute path does
   your auto-memory context name, and how many index lines does it hold?"` from two different
   git repositories on this machine that have no `.claude/settings.json` with autoMemoryDirectory
   of their own. Both answers must name ~/.claude/memory. If one of them names another directory,
   say which setting file caused it (`claude config list` in that repository, or its
   `.claude/settings.json`).
8. Finish with: the number of files and index lines in ~/.claude/memory, the names of any
   per-project directories that were skipped or had conflicts, and this reminder: the originals
   under ~/.claude/projects/*/memory/ are untouched and can be deleted by me later once I trust
   the shared directory.

9. If any repository on this machine keeps its own versioned memory (a project-scope
   `autoMemoryDirectory` in its `.claude/settings.json`), list them and ask me which to mount. For
   each I confirm, run `~/dev/recall/bin/recall mount <that memory directory>`. Say first what
   it does: it writes a marked block into `~/.claude/CLAUDE.md` with an import line and a sentence
   per mount, removes a bare duplicate import line of the same path if one exists outside the
   block, adds a symlink under `~/.claude/memory/mounts/`, and adds `mounts/` to that directory's
   `.gitignore`. Show `~/dev/recall/bin/recall status` after, including the mount cost line.
````

## Optional, outside the prompt

Both of these install software, so they are not in the paste-in block. Decide them yourself.

- **Obsidian** (`brew install --cask obsidian` on macOS, or the download from obsidian.md): open
  `~/.claude/memory` as a vault to browse the memory as a graph. Nothing in the kit needs it.
- **Capture plugin:** a separate project, github.com/konyklabs/claude-plugins, has a Claude Code
  plugin whose hooks queue the corrections you type and whose `/supervisor:reflect` command
  writes the ones you accept as memory files. It installs code that runs as hooks in every
  session; read its README first. The kit works without it.

## What to expect

- The dry run on a machine with a dozen projects takes under a second and lists every project,
  the file counts, and the index size after. The limit that matters is 200 lines or 25 KB: that
  is what loads at session start. Past it, prune the index or split rarely used facts into topic
  files that load on demand.
- A repository with its own `autoMemoryDirectory` in `.claude/settings.json` keeps it; the
  per-project default directory of such a repository is usually a symlink, and the migration
  skips it by name.
- A memory file without frontmatter fails `check`. It is still copied. Give it a `name` and a
  `description` by hand, or let `/supervisor:reflect` rewrite it when it next comes up.
