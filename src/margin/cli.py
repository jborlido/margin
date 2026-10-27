"""margin command line.

  margin open <pdf> [--source FILE] [--build CMD] [--target PANE]
        open the margin pane beside this one and tell Claude a review session started
  margin view --session FILE
        the pane itself (what `open` launches)
"""
import argparse, json, os, shutil, sys, tempfile, traceback
from datetime import datetime
from . import bridge as bridges
from .viewer import Viewer

POPPLER_TOOLS = ("pdfinfo", "pdftoppm", "pdftotext")


def launcher():
    """How to start margin again in a new pane: the dev script, or the installed module."""
    me = os.path.abspath(sys.argv[0])
    if os.path.isfile(me) and os.path.basename(me) != "__main__.py":
        return [sys.executable, me]
    return [sys.executable, "-m", "margin"]


def intro_message(pdf, source, build):
    return (f"Review session on {pdf}. "
            + (f"Source to edit: {source}. " if source else "")
            + (f"Rebuild with: `{build}`. " if build else "")
            + "Comments will arrive one at a time as messages starting with [review], each naming the page "
              "and the line they refer to. For each: find the matching span in the source, make the change, "
              "rebuild the PDF, and reply in one line. Do not ask for confirmation.")


def cmd_open(a, bridge):
    pdf = os.path.abspath(a.pdf)
    if not os.path.isfile(pdf):
        sys.exit(f"no such file: {pdf}")
    target = a.target or bridge.current_pane()
    if not target:
        sys.exit("cannot tell which pane Claude Code is in; pass --target")
    missing = [t for t in POPPLER_TOOLS if not shutil.which(t)]
    if missing:
        sys.exit(f"margin needs poppler: {', '.join(missing)} not found on PATH")
    fd, session = tempfile.mkstemp(prefix="margin-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        # PATH travels in the session file: the multiplexer server spawns the pane with its own,
        # usually minimal, environment (Zellij under Ghostty has no /opt/homebrew/bin).
        json.dump({"pdf": pdf, "source": os.path.abspath(a.source) if a.source else None,
                   "build": a.build, "target": target, "bridge": bridge.NAME,
                   "path": os.environ.get("PATH", "")}, f)
    bridge.new_pane(launcher() + ["view", "--session", session], f"margin {os.path.basename(pdf)}")
    bridge.send(target, intro_message(pdf, os.path.abspath(a.source) if a.source else None, a.build))
    print(f"margin pane opened; review session announced to {target}")


def cmd_view(a):
    d = json.load(open(a.session))
    if d.get("path"):
        os.environ["PATH"] = d["path"]
    bridge = bridges.ALL[d["bridge"]]
    try:
        Viewer(d["pdf"], bridge, d["target"]).loop()
    except Exception:
        tb = traceback.format_exc()
        with open(os.path.expanduser("~/.margin.log"), "a") as f:
            f.write(f"--- {datetime.now()}\n{tb}")
        sys.stdout.write("\r\nmargin crashed:\r\n" + tb.replace("\n", "\r\n") + "\r\npress Enter to close ")
        sys.stdout.flush()
        try:
            input()
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            os.unlink(a.session)
        except OSError:
            pass


def main(argv=None):
    p = argparse.ArgumentParser(prog="margin", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("open", help="open the margin pane for a PDF")
    o.add_argument("pdf")
    o.add_argument("--source", help="source file Claude should edit")
    o.add_argument("--build", help="command that rebuilds the PDF")
    o.add_argument("--target", help="pane id of the Claude Code pane (default: the current pane)")
    v = sub.add_parser("view", help="(internal) run the pane")
    v.add_argument("--session", required=True)
    a = p.parse_args(argv)
    if a.cmd == "view":
        return cmd_view(a)
    bridge = bridges.detect()
    if bridge is None:
        sys.exit("margin needs to run inside Zellij, tmux or WezTerm")
    cmd_open(a, bridge)
