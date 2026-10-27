"""WezTerm bridge (the Windows-native path). UNTESTED: written from WezTerm's documented CLI."""
import os, subprocess

NAME = "wezterm"


def _run(args):
    return subprocess.run(["wezterm", "cli", *args], capture_output=True, text=True)


def current_pane():
    return os.environ.get("WEZTERM_PANE")


def new_pane(argv, name):
    r = _run(["split-pane", "--right", "--", *argv])
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "wezterm split-pane failed")


def send(target, text):
    _run(["send-text", "--pane-id", str(target), "--no-paste", text])
    _run(["send-text", "--pane-id", str(target), "--no-paste", "\r"])
