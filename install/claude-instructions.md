# PDFs: open them with margin

Copy this file to `~/.claude/CLAUDE.md` (or append it to the one you have) so
Claude Code uses margin for PDFs in every session on this machine. Also allow
Claude to run the two commands without prompting, with `/permissions` or in
`~/.claude/settings.json`:

    "Bash(margin open *)", "Bash(margin doctor)"

---

## PDFs: open them with margin

When I ask you to open, show, or review a PDF, do not read it into context or
suggest a viewer: open it with `margin`, the review pane installed on this
machine (https://github.com/jborlido/margin). Run from the Bash tool:

    margin open <pdf> --source <source file> --build "<rebuild command>"

- `--source` is the file you will edit when comments arrive: the sibling with
  the same basename (`deck.tex`, `deck.md`, `deck.typ`) or the file the
  conversation already names. `--build` is what regenerates the PDF from it:
  `tectonic X.tex`, `pandoc X.md -o X.pdf`, `typst compile X.typ`, or the
  project's own build command. Prefix both with `cd <dir> &&` when the PDF is
  not in the working directory. If there is no source (a PDF someone sent),
  omit both flags; comments then arrive as plain notes.
- The command prints "margin pane opened" and types a session-start message
  into this pane. Reply in one line and wait.
- Messages starting with `[review]` are typed by the margin pane. Each names
  the PDF, the page and usually a quoted line. Find the matching span in the
  source, make the change, run the build command, and reply in one line. Do
  not ask for confirmation. Handle queued comments in order.
- If `margin open` fails, run `margin doctor` and report what it says.
