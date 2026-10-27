"""Page rendering (poppler) and terminal drawing (Kitty graphics protocol)."""
import base64, fcntl, os, re, struct, subprocess, termios

ESC = "\x1b"


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


def render_png(pdf, page, px_width, out_dir):
    """Render one page to PNG at the given pixel width; returns the file path."""
    base = os.path.join(out_dir, f"p{page}")
    run(["pdftoppm", "-png", "-f", str(page), "-l", str(page), "-scale-to-x", str(int(px_width)),
         "-scale-to-y", "-1", pdf, base])
    for f in sorted(os.listdir(out_dir)):
        if f.startswith(f"p{page}-") and f.endswith(".png"):
            return os.path.join(out_dir, f)
    raise RuntimeError("pdftoppm produced no image")


def kitty_draw(w, png_path, cols, rows, image_id=1):
    """Draw a PNG at the cursor, scaled to cols x rows cells, replacing image_id."""
    data = base64.b64encode(open(png_path, "rb").read()).decode()
    w.write(f"{ESC}_Ga=d,d=i,i={image_id},q=2{ESC}\\")
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for i, c in enumerate(chunks):
        head = f"a=T,f=100,t=d,i={image_id},c={cols},r={rows},q=2," if i == 0 else ""
        w.write(f"{ESC}_G{head}m={0 if i == len(chunks) - 1 else 1};{c}{ESC}\\")
