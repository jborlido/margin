# Installing margin

margin needs five things: a terminal that draws Kitty graphics, Zellij,
poppler, Python 3.10+, and Claude Code. One Homebrew command installs margin
together with poppler, Zellij and Python. The terminal and Claude Code are
Homebrew casks, installed separately because a formula cannot depend on a cask.

Windows is supported through WSL2: the Linux side runs everything and Windows
only supplies the terminal. See [Windows](#windows-wsl2).

## macOS

1. [Homebrew](https://brew.sh), if you do not have it.
2. The terminal and Claude Code (skip what you already have):
   ```
   brew install --cask ghostty claude-code
   ```
   Kitty or WezTerm work too; Terminal.app and iTerm2 do not draw Kitty graphics.
3. margin, with poppler, Zellij and Python pulled in as dependencies:
   ```
   brew tap jborlido/margin https://github.com/jborlido/margin
   brew install --HEAD margin
   ```
   `--HEAD` builds from the master branch; it goes away at the first tagged
   release, and the two lines will collapse into `brew install jborlido/tap/margin`
   once the tap repository exists.
4. Open Ghostty, start Zellij, start `claude` in a pane.
5. From the Claude Code prompt, check the install (the `!` prefix runs a
   shell command in that pane, which is what margin needs to see):
   ```
   ! margin doctor
   ```
   Every line should read `ok`. A `check` line means margin could not tell and
   you should verify by hand; a `MISSING` line says what to install.

## Linux

Same as macOS with [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux),
except for the two casks:

- Ghostty: your distribution's package, see
  [ghostty.org/docs/install](https://ghostty.org/docs/install). Kitty also works.
- Claude Code: `curl -fsSL https://claude.ai/install.sh | bash`

Then step 3 onwards from the macOS list.

## Windows (WSL2)

Everything runs inside WSL2 as on Linux. The one Windows-side requirement is
WezTerm, because Windows Terminal does not implement the Kitty graphics
protocol, so the page image would not show.

1. In an administrator PowerShell, install WSL2 with Ubuntu and reboot:
   ```
   wsl --install
   ```
2. Install WezTerm:
   ```
   winget install wez.wezterm
   ```
3. Create `%USERPROFILE%\.wezterm.lua` so WezTerm opens straight into Ubuntu
   and draws images:
   ```lua
   local wezterm = require 'wezterm'
   return {
     default_domain = 'WSL:Ubuntu',
     enable_kitty_graphics = true,
   }
   ```
   `enable_kitty_graphics` is off by default in WezTerm; without it the pane
   stays blank.
4. Open WezTerm. You are now in Ubuntu: follow the [Linux](#linux) steps there
   (Homebrew on Linux, the brew lines, Claude Code's installer). No Ghostty is
   needed; WezTerm is the terminal.
5. Start Zellij, start `claude` in a pane, run `! margin doctor`.

Native Windows without WSL is not supported yet. It needs a Windows console
backend for the pane and a tested WezTerm bridge; see `docs/design.md`.

## Using it

From the Claude Code prompt:

```
! margin open deck.pdf --source deck.md --build "pandoc deck.md -o deck.pdf"
```

The pane opens to the right. Click a line, type a comment, press Enter. Keys:
`/text` anchors by search, `]` and `[` change page, `Esc` clears, `q` quits.

## Updating and removing

```
brew upgrade --fetch-HEAD margin     # HEAD installs
brew uninstall margin
brew untap jborlido/margin
```
