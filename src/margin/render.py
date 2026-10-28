"""Page rendering (poppler) and terminal drawing (Kitty graphics protocol)."""
import base64, fcntl, os, re, struct, subprocess, termios, zlib

ESC = "\x1b"
HIGHLIGHT = (255, 230, 90)   # tint laid over the anchored line
HIGHLIGHT_ALPHA = 0.35
_TINT = [bytes(int(c * (1 - HIGHLIGHT_ALPHA) + t * HIGHLIGHT_ALPHA) for c in range(256)) for t in HIGHLIGHT]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def cell_size(fd):
    """(width, height) of one terminal cell in pixels; a 1:2 guess when unknown."""
    try:
        r, c, xp, yp = struct.unpack("HHHH", fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 8))
        if xp and yp and c and r:
            return xp / c, yp / r
    except Exception:
        pass
    return 10.0, 20.0


def page_count(pdf):
    m = re.search(r"Pages:\s+(\d+)", run(["pdfinfo", pdf]).stdout)
    return int(m.group(1)) if m else 1


def render_page(pdf, page, px_width, out_dir):
    """Render one page at the given pixel width; returns (width, height, RGB bytearray)."""
    base = os.path.join(out_dir, f"p{page}")
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-scale-to-x", str(int(px_width)),
                    "-scale-to-y", "-1", pdf, base], capture_output=True)
    for f in sorted(os.listdir(out_dir)):
        if f.startswith(f"p{page}-") and f.endswith(".ppm"):
            path = os.path.join(out_dir, f)
            data = open(path, "rb").read()
            os.unlink(path)
            m = re.match(rb"P6\s+(\d+)\s+(\d+)\s+\d+\s", data)
            if not m:
                raise RuntimeError("unexpected pdftoppm output")
            w, h = int(m.group(1)), int(m.group(2))
            return w, h, bytearray(data[m.end():m.end() + w * h * 3])
    raise RuntimeError("pdftoppm produced no image")


def highlight(w, h, rgb, box, pad=2):
    """A copy of the raster with the box (x0, y0, x1, y1 in pixels) tinted."""
    out = bytearray(rgb)
    x0, y0, x1, y1 = box
    x0, y0 = max(int(x0) - pad, 0), max(int(y0) - pad, 0)
    x1, y1 = min(int(x1) + pad + 1, w), min(int(y1) + pad + 1, h)
    for y in range(y0, y1):
        a, b = (y * w + x0) * 3, (y * w + x1) * 3
        for c in range(3):
            out[a + c:b:3] = out[a + c:b:3].translate(_TINT[c])
    return out


def png_encode(w, h, rgb):
    """Minimal PNG (8-bit RGB, no filtering) from a raw raster."""
    stride = w * 3
    raw = b"".join(b"\0" + rgb[y * stride:(y + 1) * stride] for y in range(h))

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 3)) + chunk(b"IEND", b""))


def kitty_draw(w, png, cols, rows, image_id, old_id=None):
    """Draw a PNG at the cursor, scaled to cols x rows cells, then drop the previous image.

    Sending the new image before deleting the old one avoids a blank frame between them.
    C=1 keeps the cursor where it was, so the caller positions text explicitly.
    """
    data = base64.b64encode(png).decode()
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for i, c in enumerate(chunks):
        head = f"a=T,f=100,t=d,i={image_id},c={cols},r={rows},C=1,q=2," if i == 0 else ""
        w.write(f"{ESC}_G{head}m={0 if i == len(chunks) - 1 else 1};{c}{ESC}\\")
    if old_id is not None:
        w.write(f"{ESC}_Ga=d,d=i,i={old_id},q=2{ESC}\\")
