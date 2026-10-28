# margin — status and next steps

Last updated: 2026-10-28. Keep this file current; it is the hand-off between
sessions.

## Where things stand

- The loop works end to end on João's Mac, confirmed in a real review session
  on 2026-10-28: click, comment, `[review]` message in Claude Code, source
  edit, rebuild, pane redraw. First trial findings (PATH, flicker, no on-page
  highlight) are fixed and looked better in a quick second run; João will
  validate properly on 2026-10-29. Two comments were acted on in the trial
  (a tone rewrite and removing an old entry from the scratch CV copy).
- First commit pushed to `github.com/jborlido/margin` (master).
- `uv` is not installed on João's Mac; the dev launcher `bin/margin` works
  without it. The installer will add uv later.

## Next steps, in order

1. **UX trial on the CV.** João runs, from the Claude Code prompt:
   `! ~/dev/personal/margin/bin/margin open ~/dev/personal/margin/work/cv/resume.pdf --source ~/dev/personal/margin/work/cv/resume.tex --build "cd ~/dev/personal/margin/work/cv && tectonic resume.tex"`
   Questions the trial must answer: does a click land on the intended line;
   does typing feel immediate; does the page redraw by itself after the
   rebuild; do Claude's edits match the comment. Fix what the trial shows
   before adding features.
2. **Pane ergonomics** likely needed after the trial: let a comment cover a
   region (drag) rather than one line; keep a scrollable history of sent
   comments with their state (sent / Claude replied / rebuilt); `g <n>`
   go-to page. Done 2026-10-28: the anchored line is tinted on the page
   image, and typing no longer re-sends the image (first trial found the
   pane flickering on every keystroke and giving no on-page feedback).
3. **`margin doctor`**: check poppler, multiplexer, Kitty passthrough, and
   that the bridge can reach the Claude pane.
4. **Installers**: `install/install.sh` (macOS + Linux) then `install.ps1`
   (Windows native via WezTerm; `--wsl` route). Design in `docs/design.md`.
   Keep the repo clonable onto João's backup drive: a fresh Mac must be able
   to run the installer with nothing but the drive.
5. **tmux and WezTerm bridges**: test them; they are written blind.
6. **Claude Code plugin** (`adapters/claude-plugin/`): a `/margin <pdf>`
   command that opens the pane and attaches source path, build command and
   page text as hidden context. Optional; the Zellij bridge is the foundation.
7. **Packaging**: `uv tool install` from a release tag; later maybe a single
   binary if the Python runtime turns out to be an installer burden.

## Decisions so far

| Date | Decision | Why |
|---|---|---|
| 2026-10-21 | Stay in the terminal; no browser, no Acrobat | João's whole workflow is Ghostty + Zellij; the browser-based artifact review broke the flow |
| 2026-10-21 | The PDF is a rendering; Claude edits the source and rebuilds | Anchoring to a quoted text line works for LaTeX, markdown, pptx scripts alike |
| 2026-10-21 | Comments reach Claude by being typed into its pane via the multiplexer CLI | Zero dependency on Claude Code internals; survives Claude Code updates |
| 2026-10-21 | Claude Code plugin is an optional adapter, not the foundation | Its API (pane images, `$.prompt.submit`) exists in 2.1.292 but is partly undocumented and version-bound |
| 2026-10-21 | Per-OS stack: Ghostty+Zellij on macOS/Linux, WezTerm on Windows (WSL optional) | Ghostty has no Windows build; Zellij needs WSL on Windows; WezTerm has Kitty graphics and a pane-targeting CLI |
| 2026-10-21 | Python, stdlib only, uv for install | Iteration speed now; a Rust rewrite is cheap once behaviour settles |
| 2026-10-27 | Name: `margin` | Reads naturally (`margin open deck.pdf`); free on PyPI, Homebrew and GitHub |
| 2026-10-27 | License: PolyForm Noncommercial 1.0.0 | Public repo, free for personal/noncommercial use, João keeps commercial rights |
| 2026-10-27 | Session details in a JSON file, not argv | Zellij re-splits the pane command on whitespace and broke `--build "cd x && make"` |
| 2026-10-27 | The caller's PATH travels in the session file and the pane applies it | The Zellij server spawns panes with its own minimal PATH (no `/opt/homebrew/bin`), so `pdfinfo` was not found; `open` also checks for poppler up front |

## Environment facts (João's Mac)

- macOS 27.0.1, Ghostty 1.3.1 (config runs `~/.local/bin/zjboot`, option-as-alt),
  Zellij 0.45.1 with custom keybinds (`clear-defaults=true`; pane mode `r` =
  new pane right), layouts in `~/.config/zellij/layouts/` with one full-width
  pane per project tab and a zjstatus hint bar.
- Claude Code 2.1.292, runs in pane `terminal_0` of Zellij session `main`.
- Installed: poppler (`pdftoppm`, `pdftotext`, `pdfinfo`), pandoc, fzf,
  tectonic (XeTeX-based; builds the CV in ~1 s). Not installed: uv, xelatex,
  mutool, timg/chafa/viu, Skim.
- Kitty graphics pass through Zellij inside Ghostty (verified by drawing a
  page in a shell pane).
- The Zellij server's PATH is `/usr/bin:/bin:/usr/sbin:/sbin:/Applications/Ghostty.app/Contents/MacOS`;
  panes it spawns via `zellij action new-pane` inherit it, not the shell's.
- João's documents: the CV is LaTeX (`resume.tex`, needs the Avenir Next
  system font and `photo.png`); other documents will come from pandoc or the
  pptx skill. Source of truth for the CV is the knowledge-vault repo; the copy
  in `work/cv/` is scratch.

## Open questions

- Will click-anchoring be precise enough on dense pages, or is a drag-region
  needed?
- Should comments be batched (several comments, one "go") as an option, for
  cases where Claude's rebuild between every comment is a distraction?
- Where should the standing "how to act on [review] messages" instruction live
  for documents outside this repo: user-level CLAUDE.md, the plugin, or the
  session-start message only (current)?
