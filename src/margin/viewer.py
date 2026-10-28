"""The margin pane: page image, click-to-anchor, comment input, rebuild watch."""
import os, re, select, shutil, signal, sys, termios, tty
from datetime import datetime
from .render import ESC, cell_size, page_count, render_page, highlight, png_encode, kitty_draw
from .anchor import page_lines, nearest_line, search_line


class Viewer:
    def __init__(self, pdf, bridge, target):
        self.pdf, self.bridge, self.target = os.path.abspath(pdf), bridge, target
        self.page, self.pages = 1, page_count(self.pdf)
        self.anchor = None          # (text, line index)
        self.buf = ""
        self.log = []
        self.status = ""
        self.mtime = os.path.getmtime(self.pdf)
        self.pending_mtime = None
        self.tmp = os.path.join("/tmp", f"margin-{os.getpid()}")
        os.makedirs(self.tmp, exist_ok=True)
        self.lines, self.page_size = page_lines(self.pdf, self.page)
        self.img_cols = self.img_rows = 1
        self.raster = None          # (key, width, height, rgb) of the rendered page
        self.png_cache = {}         # (key, anchor index) -> encoded PNG
        self.image_id = 1           # alternates 1/2 so the new image lands before the old is dropped
        self.drawn_size = None
        self.dirty = True           # footer text needs redrawing
        self.redraw_image = True    # page image needs re-sending (page, anchor, size or PDF changed)

    # layout -------------------------------------------------------------
    def layout(self):
        cols, rows = shutil.get_terminal_size()
        cw, ch = cell_size(sys.stdout.fileno())
        avail_rows = max(rows - 7, 5)
        pw, ph = self.page_size
        aspect = ph / pw
        c = cols
        r = int((c * cw * aspect) / ch + 0.999)
        if r > avail_rows:
            r = avail_rows
            c = max(int((r * ch) / (aspect * cw)), 10)
        self.img_cols, self.img_rows = c, r
        return cols, rows, cw

    def draw(self):
        """Redraw the footer; re-send the page image only when something on it changed."""
        w = sys.stdout
        cols, rows, cw = self.layout()
        if self.redraw_image:
            if self.drawn_size != (self.img_cols, self.img_rows):
                w.write(f"{ESC}[2J")
                self.drawn_size = (self.img_cols, self.img_rows)
            w.write(f"{ESC}[H")
            try:
                self.draw_image(w, cw)
            except Exception as e:
                w.write(f"(render failed: {e})")
            self.redraw_image = False
        y = self.img_rows + 1
        name = os.path.basename(self.pdf)

        def line(row, text):
            w.write(f"{ESC}[{row};1H{ESC}[2K{text}")

        line(y, f"{ESC}[1m{name}{ESC}[0m  page {self.page}/{self.pages}   "
                f"{ESC}[2m[ ] page  / search  click anchor  Enter send  q quit{ESC}[0m  {self.status}")
        recent = self.log[-3:]
        for i in range(3):
            line(y + 1 + i, f"{ESC}[2m{recent[i][:cols - 1]}{ESC}[0m" if i < len(recent) else "")
        anchor = f"«{self.anchor[0][:cols - 12]}»" if self.anchor else "(whole page)"
        line(y + 4, f"{ESC}[36manchor{ESC}[0m {anchor}")
        line(y + 5, f"{ESC}[33m>{ESC}[0m {self.buf}")
        w.write(f"{ESC}[{y + 5};{3 + len(self.buf)}H")
        w.flush()
        self.dirty = False

    def draw_image(self, w, cw):
        key = (self.page, int(self.img_cols * cw), self.mtime)
        if not self.raster or self.raster[0] != key:
            self.raster = (key, *render_page(self.pdf, self.page, key[1], self.tmp))
            self.png_cache.clear()
        _, iw, ih, rgb = self.raster
        which = self.anchor[1] if self.anchor else None
        png = self.png_cache.get(which)
        if png is None:
            if which is not None:
                pw, ph = self.page_size
                _, x0, y0, x1, y1 = self.lines[which]
                sx, sy = iw / pw, ih / ph
                rgb = highlight(iw, ih, rgb, (x0 * sx, y0 * sy, x1 * sx, y1 * sy))
            png = self.png_cache[which] = png_encode(iw, ih, rgb)
        old, self.image_id = self.image_id, 3 - self.image_id
        kitty_draw(w, png, self.img_cols, self.img_rows, self.image_id, old)

    def set_anchor(self, anchor):
        if anchor != self.anchor:
            self.anchor = anchor
            self.redraw_image = True
        self.dirty = True

    # actions ------------------------------------------------------------
    def goto(self, page):
        self.page = max(1, min(self.pages, page))
        self.lines, self.page_size = page_lines(self.pdf, self.page)
        self.anchor = None
        self.redraw_image = self.dirty = True

    def anchor_at_cell(self, x, y):
        i = nearest_line(self.lines, self.page_size, x, y, self.img_cols, self.img_rows)
        if i is not None:
            self.set_anchor((self.lines[i][0], i))

    def anchor_search(self, needle):
        i = search_line(self.lines, needle)
        if i is None:
            self.status = f"not found: {needle}"
            self.dirty = True
        else:
            self.status = ""
            self.set_anchor((self.lines[i][0], i))

    def send(self, comment):
        where = f"page {self.page}"
        if self.anchor:
            where += f", at the line «{self.anchor[0]}»"
        self.bridge.send(self.target, f"[review] {os.path.basename(self.pdf)}, {where}: {comment}")
        self.log.append(f"{datetime.now():%H:%M:%S} sent  {where}: {comment}")
        self.set_anchor(None)

    def check_rebuilt(self):
        try:
            m = os.path.getmtime(self.pdf)
        except FileNotFoundError:
            return
        if m != self.mtime:
            if self.pending_mtime == m:            # unchanged for one tick: the rebuild finished
                self.mtime, self.pending_mtime = m, None
                self.pages = page_count(self.pdf)
                self.page = min(self.page, self.pages)
                self.lines, self.page_size = page_lines(self.pdf, self.page)
                self.status = f"{ESC}[32mrebuilt {datetime.now():%H:%M:%S}{ESC}[0m"
                self.redraw_image = self.dirty = True
            else:
                self.pending_mtime = m

    # main loop ----------------------------------------------------------
    def loop(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setraw(fd)
        sys.stdout.write(f"{ESC}[?1049h{ESC}[?1000h{ESC}[?1006h{ESC}[?25h")
        signal.signal(signal.SIGWINCH, lambda *_: setattr(self, "redraw_image", True) or setattr(self, "dirty", True))
        try:
            while True:
                if self.dirty or self.redraw_image:
                    self.draw()
                r, _, _ = select.select([fd], [], [], 0.5)
                if not r:
                    self.check_rebuilt()
                    continue
                data = os.read(fd, 1024).decode(errors="ignore")
                if self.handle(data) is False:
                    break
        finally:
            sys.stdout.write(f"{ESC}[?1000l{ESC}[?1006l{ESC}[?1049l")
            sys.stdout.flush()
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            shutil.rmtree(self.tmp, ignore_errors=True)

    def handle(self, data):
        i = 0
        while i < len(data):
            ch = data[i]
            if ch == ESC:
                m = re.match(r"\x1b\[<(\d+);(\d+);(\d+)([mM])", data[i:])
                if m:
                    btn, x, y, kind = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
                    if kind == "M" and btn == 0:
                        self.anchor_at_cell(x, y)
                    i += m.end()
                    continue
                if data[i:i + 2] == f"{ESC}[":          # any other CSI sequence: skip it
                    j = i + 2
                    while j < len(data) and not data[j].isalpha():
                        j += 1
                    i = j + 1
                    continue
                self.buf = ""
                self.set_anchor(None)
                i += 1
                continue
            if ch in ("\r", "\n"):
                text = self.buf.strip()
                self.buf = ""
                if text.startswith("/"):
                    self.anchor_search(text[1:].strip())
                elif text:
                    self.send(text)
                self.dirty = True
            elif ch == "\x7f":
                self.buf = self.buf[:-1]; self.dirty = True
            elif ch == "\x15":
                self.buf = ""; self.dirty = True
            elif ch == "\x03":
                return False
            elif ch == "q" and not self.buf:
                return False
            elif ch == "]" and not self.buf:
                self.goto(self.page + 1)
            elif ch == "[" and not self.buf:
                self.goto(self.page - 1)
            elif ch == "r" and not self.buf:
                self.raster, self.redraw_image, self.dirty = None, True, True
            elif ch.isprintable():
                self.buf += ch; self.dirty = True
            i += 1
        return True
