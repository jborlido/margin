"""Zellij bridge (tested: Zellij 0.45, Ghostty 1.3, macOS)."""
import os, subprocess

NAME = "zellij"


def _run(args):
    return subprocess.run(["zellij", "action", *args], capture_output=True, text=True)


def normalize(target):
    target = str(target)
    return target if target.startswith(("terminal_", "plugin_")) else f"terminal_{target}"


def current_pane():
    pid = os.environ.get("ZELLIJ_PANE_ID")
    return normalize(pid) if pid is not None else None


def new_pane(argv, name):
    # Zellij re-splits the command on whitespace, so argv must not carry arguments with spaces.
    r = _run(["new-pane", "--direction", "right", "--close-on-exit", "--name", name, "--", *argv])
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "zellij new-pane failed")


def send(target, text):
    _run(["write-chars", "--pane-id", normalize(target), text])
    _run(["write", "--pane-id", normalize(target), "13"])
