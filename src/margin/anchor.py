"""Mapping a click or a search to a text line on the page."""
import xml.etree.ElementTree as ET
from .render import run


def page_lines(pdf, page):
    """[(text, xMin, yMin, xMax, yMax)] and (page_w, page_h), from poppler's bbox output."""
    xml = run(["pdftotext", "-bbox-layout", "-f", str(page), "-l", str(page), pdf, "-"]).stdout
    root = ET.fromstring(xml)
    pw = ph = 1.0
    lines = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "page":
            pw, ph = float(el.get("width")), float(el.get("height"))
        elif tag == "line":
            words = [w.text or "" for w in el.iter() if w.tag.split("}")[-1] == "word"]
            text = " ".join(words).strip()
            if text:
                lines.append((text, *[float(el.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")]))
    return lines, (pw, ph)


def nearest_line(lines, page_size, x, y, img_cols, img_rows):
    """Index of the line nearest to terminal cell (x, y) over an image of img_cols x img_rows."""
    if not lines or x > img_cols or y > img_rows:
        return None
    pw, ph = page_size
    px = (x - 0.5) / img_cols * pw
    py = (y - 0.5) / img_rows * ph

    def dist(l):
        _, x0, y0, x1, y1 = l
        dx = max(x0 - px, 0, px - x1)
        dy = max(y0 - py, 0, py - y1)
        return dx * dx + dy * dy

    return min(range(len(lines)), key=lambda i: dist(lines[i]))


def search_line(lines, needle):
    needle = needle.lower()
    for i, l in enumerate(lines):
        if needle in l[0].lower():
            return i
    return None
