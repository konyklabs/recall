# Setup prompt

Paste the block below as the first message of a Claude Code session on the machine to set up.
Start the session in your home directory or above your checkouts, not inside a repository that
sets its own memory directory. The session needs `git` and `python3` (3.9 or newer).

Everything it changes: one key in `~/.claude/settings.json`, a new directory with a git
repository in it, and a checkout of this kit. It deletes nothing. Replace the directory path if
you want the memory elsewhere.

````
Set up a shared Claude Code memory directory on this machine with the recall kit. Do these steps
in order, show the command and its output for each, and stop at any step whose output you cannot
show.

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
6. Commit the memory directory: `git -C ~/.claude/memory add -A && git -C ~/.claude/memory commit -m "Gather this machine's auto memory"`.
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

Optional, only if I say yes when you ask at the end, as one question: install Obsidian
(`brew install --cask obsidian` on macOS) and open ~/.claude/memory as a vault; and install the
capture plugin with `claude plugin marketplace add konyklabs/claude-plugins` then
`claude plugin install supervisor@konyklabs-plugins`, and tell me `/supervisor:reflect` is how
queued corrections become memory.
````

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
