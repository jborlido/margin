"""Multiplexer bridges: open the margin pane and type comments into the Claude Code pane.

Each bridge module exposes:
    current_pane() -> str | None     id of the pane this process runs in
    new_pane(argv, name)             open a pane to the right running argv
    send(target, text)               type text into pane `target` and press Enter
"""
import os
from . import zellij, tmux, wezterm

ALL = {"zellij": zellij, "tmux": tmux, "wezterm": wezterm}


def detect():
    if os.environ.get("ZELLIJ_SESSION_NAME"):
        return zellij
    if os.environ.get("TMUX"):
        return tmux
    if os.environ.get("WEZTERM_PANE"):
        return wezterm
    return None
