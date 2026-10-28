# margin

Notes in the margin, for documents Claude Code writes.

`margin` opens a PDF in a terminal pane next to a running Claude Code session.
You click a line on the page, type a comment, press Enter, and the comment
reaches Claude as a message that names the page and the exact line. Claude
edits the source, rebuilds the PDF, and the pane redraws. No browser, no
Acrobat, no "go read my comments" prompt.

**Status: prototype.** The loop works on macOS with Ghostty + Zellij. Other
terminals, tmux/WezTerm bridges, the Claude Code plugin and the installers
are planned; see [docs/design.md](docs/design.md).

## How it works

```
┌──────────────────────────┐ ┌──────────────────────────────┐
│ claude  (stock)          │ │ margin pane                  │
│                          │ │ page image · click = anchor  │
│                          │ │ > your comment_              │
└──────────────────────────┘ └──────────────────────────────┘
          ▲ comment typed into this pane by id ──────┘
```

- Pages are rendered with poppler and drawn with the Kitty graphics protocol.
- A click is mapped to the nearest text line using poppler's bounding boxes.
- The comment is typed into the Claude Code pane by the multiplexer's CLI
  (`zellij action write-chars --pane-id`), so nothing depends on Claude Code
  internals and a Claude Code update cannot break it.
- The pane watches the PDF and redraws when the rebuild lands.

## Install

```
brew tap jborlido/margin https://github.com/jborlido/margin
brew trust jborlido/margin
brew install --HEAD margin
```

That brings in poppler, Zellij and Python. You also need a terminal that draws
Kitty graphics (Ghostty, Kitty or WezTerm) and Claude Code. Full steps for
macOS, Linux and Windows (via WSL2) are in [install/README.md](install/README.md).
Check an install with `! margin doctor` from the Claude Code prompt.

## Try it

From the Claude Code prompt (so the pane targets that session):

```
! margin open deck.pdf --source deck.md --build "pandoc deck.md -o deck.pdf"
```

Keys in the pane: click to anchor, `/text` to anchor by search, Enter to send,
`]` `[` to change page, `Esc` to clear, `q` to quit.

## License

PolyForm Noncommercial 1.0.0. Free for personal and noncommercial use; commercial
use requires permission from the author. See [LICENSE.md](LICENSE.md).

Required Notice: Copyright (c) 2026 João Borlido (https://github.com/jborlido/margin)
