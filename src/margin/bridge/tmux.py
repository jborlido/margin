"""tmux bridge. UNTESTED: written from tmux's documented CLI, not yet exercised."""
import os, subprocess

NAME = "tmux"


def _run(args):
    return subprocess.run(["tmux", *args], capture_output=True, text=True)


def current_pane():
    return os.environ.get("TMUX_PANE")


def new_pane(argv, name):
    r = _run(["split-window", "-h", "-d", *argv])
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "tmux split-window failed")


def send(target, text):
    _run(["send-keys", "-t", target, "-l", text])
    _run(["send-keys", "-t", target, "Enter"])
