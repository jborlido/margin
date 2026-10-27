# margin — instructions for Claude Code sessions in this repo

Read `docs/status.md` first (where things stand, what is next), then
`docs/design.md` (architecture and the reasoning behind it).

## What this is

A terminal tool: a PDF opens in a pane beside Claude Code; the user clicks a
line, types a comment, presses Enter; the comment is typed into the Claude Code
pane as a message naming the page and the quoted line; Claude edits the source,
rebuilds, and the pane redraws. Owner: João Borlido. License: PolyForm
Noncommercial 1.0.0 (keep the Required Notice line in README and LICENSE).

## Working rules

- **Pure stdlib Python, 3.10+.** No dependencies until there is a reason that
  survives review; the tool must install on a fresh machine with nothing but
  Python, poppler and the multiplexer.
- **Hosts are plugged into, never modified.** Zellij, tmux, WezTerm, Ghostty
  and Claude Code stay stock. All host-specific code lives in `src/margin/bridge/`
  (multiplexers) and `adapters/` (Claude Code plugin, layouts). The Zellij
  bridge is the only tested one; keep the tmux and WezTerm bridges marked
  UNTESTED in their docstrings until someone runs them.
- **Do not pass user strings through a pane command line.** Zellij re-splits
  `new-pane -- cmd` on whitespace. Session details go in the JSON session file.
- **Do not run `margin open` from the Bash tool.** Claude Code's permission
  classifier blocks it, because it types into the session. Ask the user to run
  it from the prompt with the `!` prefix instead:
  `! ~/dev/personal/margin/bin/margin open <pdf> --source <src> --build "<cmd>"`
- **Smoke test before committing viewer changes** (no real terminal needed):
  ```
  python3 -c "import json; json.dump({'pdf':'work/cv/resume.pdf','source':'work/cv/resume.tex','build':'cd work/cv && tectonic resume.tex','target':'terminal_0','bridge':'zellij'}, open('/tmp/margin-smoke.json','w'))"
  (sleep 2; printf 'q') | script -q /dev/null bin/margin view --session /tmp/margin-smoke.json > /tmp/margin-smoke.out 2>&1
  grep -a -c '_Ga=T' /tmp/margin-smoke.out     # 1 = a page was drawn
  grep -a -c 'margin crashed' /tmp/margin-smoke.out   # must be 0
  ```
  `work/` is gitignored scratch space; `work/cv/` holds a copy of João's CV
  (`resume.tex`, `photo.png`, `resume.pdf`, builds with `tectonic resume.tex`)
  used as the test document. Never edit the original in the knowledge-vault repo.
- Crashes in the pane are appended to `~/.margin.log`.
- Commit on master is fine while the project is a prototype; João pushes.

## Acting on review comments

When a message starting with `[review]` arrives, it was typed by the margin
pane. It names the PDF, the page and usually a quoted line. Find the matching
span in the source named in the session-start message, make the change, run
the build command, and reply in one line. Do not ask for confirmation. Comments
may queue while you work; handle them in order.
