# The 7-sticker stats board ("In production"): 4 tilted pastel cards on top + 3 wide tilted cards below.
# Exact same sticker-board geometry, shadows, rotations and inline vector icons as ZazaGdev's board.
from cards import long_date
from svgkit import Svg, wrap

FILLS = ["lx", "li", "rd", "x", "bd", "yt", "li"]
ROT = [-1.2, 1, -0.8, 1.2, -1, 0.8, -1.2]


def counters(P):
    return [(c["value"], c["label"], c["icon"]) for c in P["board"]["counters"]]


def board_label(data, P):
    parts = [f"{c['value']} {c['label']}" for c in P["board"]["counters"]]
    return f"{P['board']['title']}: " + ", ".join(parts) + "."


def sticker(s, x, y, w, h, fill, rot):
    s.add(f'<g transform="rotate({rot} {x + w / 2:.1f} {y + h / 2:.1f})">')
    s.rect(x + 4, y + 4, w, h, "line", 18)
    s.rect(x, y, w, h, fill, 18, "line", 2)


# Simple 24 x 24 icons: (path, closed). Closed shapes get the token fill, all get the ink outline.
ICONS = {
    "cloud": [("M6.5 19H18A4 4 0 0 0 18.8 11.1A5.5 5.5 0 0 0 8.1 9.5A4 4 0 0 0 6.5 19Z", True)],
    "globe": [("M12 3A9 9 0 1 1 11.99 3Z", True), ("M3.6 9H20.4", False), ("M3.6 15H20.4", False),
              ("M12 3C9.5 6 9.5 18 12 21C14.5 18 14.5 6 12 3", False)],
    "flame": [("M12 2.5C12.5 7 18 9 18 14.5A6 6 0 0 1 6 14.5C6 11.5 8 10 9 8C10 10 11 10.5 12 9.5C12.5 7 12 4.5 12 2.5Z", True)],
    "trophy": [("M7 4H17V10A5 5 0 0 1 7 10Z", True), ("M7 6H4V8A3 3 0 0 0 7 11", False),
               ("M17 6H20V8A3 3 0 0 1 17 11", False), ("M12 15V19", False), ("M8 20.5H16", False)],
    "calendar": [("M5 5H19A2 2 0 0 1 21 7V19A2 2 0 0 1 19 21H5A2 2 0 0 1 3 19V7A2 2 0 0 1 5 5Z", True),
                 ("M3 10H21", False), ("M8 3V7", False), ("M16 3V7", False)],
    "chart": [("M4 20V12H8V20Z", True), ("M10 20V5H14V20Z", True), ("M16 20V9H20V20Z", True)],
    "bolt": [("M13 2L4.5 13.5H11.5L10.5 22L19.5 10.5H12.5Z", True)],
}


def icon(s, kind, x, y, size, fill="pop"):
    """A sticker-style icon: ink outline from the tokens, one token fill, drawn from inline paths."""
    k = size / 24
    parts = "".join(f'<path d="{d}" fill="{s.col(fill) if closed else "none"}"/>' for d, closed in ICONS[kind])
    s.add(f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})" stroke="{s.col("line")}" stroke-width="{1.9 / k:.2f}" '
          f'stroke-linecap="round" stroke-linejoin="round">{parts}</g>')


def stats_board(t, data, P):
    cs = counters(P)
    W = 880
    s = Svg(W, 340, t, board_label(data, P))
    s.board()
    s.text(32, 54, P["board"]["title"], "f700", 30)
    prefix = P["board"].get("subtitle_prefix", "")
    stamp = f"{prefix} · redrawn nightly · {long_date(data['today'])}" if prefix else f"redrawn every night · {long_date(data['today'])}"
    s.text(848, 52, stamp, "m400", 15, "muted", "end")
    for i in range(4):
        x, y = 32 + i * 208, 78
        sticker(s, x, y, 190, 138, FILLS[i], ROT[i])
        num, lab, ic = cs[i]
        icon(s, ic, x + 190 - 14 - 30, y + 10, 30)
        s.text(x + 16, y + 70, num, "f700", 40)
        ly = y + 94
        for line in wrap(lab, "m400", 15, 160)[:3]:
            s.text(x + 16, ly, line, "m400", 15)
            ly += 19
        s.add("</g>")
    widths = (256, 256, 264)
    xs = (32, 308, 584)
    for j in range(3):
        x, y = xs[j], 238
        w = widths[j]
        sticker(s, x, y, w, 66, FILLS[4 + j], ROT[4 + j] * 0.6)
        num, lab, ic = cs[4 + j]
        icon(s, ic, x + 14, y + 17, 32)
        nw = s.text(x + 54, y + 43, num, "f700", 30)
        s.text(x + 54 + nw + 10, y + 40, lab, "m400", 14)
        s.add("</g>")
    return s
