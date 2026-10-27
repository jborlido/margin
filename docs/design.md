# margin — design

## Problem

Documents that Claude Code generates (PDF from LaTeX, markdown, pptx, ...) get
reviewed by hand in Acrobat: open the app, write comments (the comment box is
flaky), remember to save, return to the terminal, ask Claude to read the
comments, wait for everything to be processed in one batch. Context switches
and batch latency, for a loop that should feel like a conversation.

## Goal

Stay in the terminal (Ghostty + Zellij on macOS; equivalents elsewhere). See
the rendered page beside Claude Code. Comment on a specific part of it. Have
each comment reach Claude immediately as a message about that part. See the
rebuilt page as soon as Claude's edit lands.

## Principles

1. **The PDF is a rendering; the source is what Claude edits.** A comment is
   anchored to a quoted text line, which Claude can find in any source format.
2. **One standalone tool, thin adapters.** `margin` owns rendering, anchoring,
   the comment UI and the rebuild watch. Zellij / tmux / WezTerm and Claude
   Code are only plugged into, never modified, so host updates cannot remove it.
3. **The bridge depends on nothing inside Claude Code.** Comments are typed into
   the Claude Code pane through the multiplexer's CLI. Claude Code already
   queues messages typed mid-turn, so comments line up while it works.
4. **Uniform behaviour, per-platform stack.** Ghostty has no Windows build and
   Zellij does not run natively on Windows, so the stack differs per OS while
   the tool and the UX stay the same.

## Architecture

```
┌──────────────────────────┐ ┌──────────────────────────────┐
│ claude  (stock binary)   │ │ margin pane  (this tool)     │
│                          │ │ page image · click = anchor  │
│                          │ │ > comment_                   │
└──────────────────────────┘ └──────────────────────────────┘
          ▲ typed into this pane by id ──────────┘
```

- `render.py` — poppler page rendering, Kitty graphics drawing, cell metrics.
- `anchor.py` — poppler bounding boxes; click → nearest line; text search.
- `viewer.py` — the pane: raw-mode input, SGR mouse, rebuild watch (mtime).
- `bridge/` — `zellij` (tested), `tmux`, `wezterm` (untested); each gives
  `current_pane`, `new_pane`, `send`.
- `cli.py` — `open` (writes a session file, opens the pane, announces the
  session to Claude) and `view` (runs the pane).

Session details travel in a JSON file, not argv: Zellij re-splits a pane
command on whitespace, which broke `--build "cd x && make"`.

Optional later: a Claude Code plugin with `/margin deck.pdf` that opens the pane
and attaches the source path, build command and page text as hidden context.
If the plugin API changes, the Zellij path still works.

## Platform matrix

| | Terminal | Multiplexer | Bridge | Images |
|---|---|---|---|---|
| macOS | Ghostty | Zellij | `zellij action write-chars --pane-id` | Kitty |
| Linux | Ghostty | Zellij | same | Kitty |
| Windows native | WezTerm | WezTerm panes | `wezterm cli send-text --pane-id` | Kitty |
| Windows via WSL2 | WezTerm on host | Zellij in WSL | Zellij | Kitty |

## Installers (planned)

- `install/install.sh` — macOS + Linux: brew / apt / dnf / pacman; Ghostty,
  Zellij, poppler, uv, Claude Code, margin, layout + config defaults (never
  overwriting existing config).
- `install/install.ps1` — Windows native (winget: WezTerm, uv, Claude Code;
  poppler via scoop/winget); `--wsl` sets up WSL2 and runs `install.sh` inside.
- `margin doctor` — checks dependencies, runs the graphics passthrough test,
  confirms the bridge can reach a Claude pane.

## Verified so far (2026-10-21 → 2026-10-27, macOS 27, Ghostty 1.3.1, Zellij 0.45.1)

- Kitty graphics pass through Zellij inside Ghostty.
- `zellij action write-chars --pane-id` delivers a message into a running
  Claude Code session; Claude receives it as a user message.
- Claude Code's own plugin API (2.1.292) can also submit prompts and draw PNGs
  in a pane, but it is undocumented in parts and version-bound; kept as the
  optional adapter, not the foundation.
- poppler's `pdftotext -bbox-layout` gives per-line boxes good enough for
  click-to-line anchoring on a two-column CV.
- Running `margin open` from Claude Code's own Bash tool is blocked by Claude
  Code's permission classifier (it types into the session). Launch it from the
  prompt with the `!` prefix instead.

## License

PolyForm Noncommercial 1.0.0.
