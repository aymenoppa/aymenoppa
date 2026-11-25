# Phone variants for every picture (<source media="(max-width: 600px)">).
import os

from board import FILLS, ROT, board_label, counters, icon, sticker
from cards import (app_fact, app_label, arrow, fit_size, hero_label, name_line,
                   sticker_link, terminal_height, whoami_label, whoami_lines, _terminal)
from svgkit import HERE, Svg, img_b64, mix, text_width, wrap


def hero_phone(t, data, P):
    tag_lines = wrap(P["tagline"], "f500", 20, 388)
    chip_y0 = 136 + 27 * len(tag_lines)
    places, cx, cy = [], 26, chip_y0
    for lab, fill in P["tags"]:
        w = text_width(lab, "f600", 15) + 26
        if cx + w > 414:
            cx, cy = 26, cy + 42
        places.append((cx, cy, lab, fill))
        cx += w + 12
    s = Svg(440, int(cy + 32 + 28), t, hero_label(P))
    s.board()
    s.alogo(26, 26, 76)
    name_line(s, 116, 92, P["name"], 40)
    host = P["site_host"]
    sw = max(100, int(text_width(host, "f700", 15) + 22))
    sticker_link(s, 418 - sw, 14, sw, 32, host, 15)
    ly = 134
    for line in tag_lines:
        s.text(26, ly, line, "f500", 20, "muted")
        ly += 27
    for px, py, lab, fill in places:
        s.chip(px, py, lab, fill, "f600", 15, 32, 13, 2, 9, 3)
    return s


def whoami_phone(t, data, P):
    L = whoami_lines(data, P, phone=True)
    L += [[("$ ", "pop", "m500")]]
    h = terminal_height(L, 16, 26, 408, 18)
    s = Svg(440, h + 36, t, whoami_label(data, P))
    s.board()
    _terminal(s, 14, 16, 408, h, P["terminal_title"], L, 16, 26, 18)
    return s


def stats_board_phone(t, data, P):
    cs = counters(P)
    s = Svg(440, 534, t, board_label(data, P))
    s.board()
    s.text(26, 54, P["board"]["title"], "f700", 30)
    s.text(414, 52, P["board"].get("subtitle_phone", "redrawn nightly"), "m400", 15, "muted", "end")
    # the first card, full width
    sticker(s, 26, 78, 388, 100, FILLS[0], ROT[0])
    num0, lab0, ic0 = cs[0]
    s.text(44, 132, num0, "f700", 48)
    nw = text_width(num0, "f700", 48)
    icon(s, ic0, 26 + 388 - 14 - 32, 78 + 12, 32)
    for k, line in enumerate(wrap(lab0, "m400", 16, 388 - 44 - nw - 16 - 36)[:3]):
        s.text(44 + nw + 14, 118 + k * 20, line, "m400", 16)
    s.add("</g>")
    y = 198
    for k in range(1, 7):
        col, row = (k - 1) % 2, (k - 1) // 2
        x, yy = 26 + col * 200, y + row * 106
        sticker(s, x, yy, 188, 92, FILLS[k], ROT[k])
        num, lab, ic = cs[k]
        icon(s, ic, x + 188 - 12 - 24, yy + 8, 24)
        s.text(x + 14, yy + 42, num, "f700", 32)
        for m, line in enumerate(wrap(lab, "m400", 15, 188 - 28)[:2]):
            s.text(x + 14, yy + 64 + m * 18, line, "m400", 15)
        s.add("</g>")
    return s


def app_phone(t, a, data, P):
    s = Svg(440, 236, t, app_label(a, app_fact(a, data, P)))
    s.board(stroke=False)
    x, y, w, h = 16, 16, 408, 204
    s.card(x, y, w, h, mix(s.col(a["tint"]), s.col("card"), 0.38))
    row_y, row_h, ic_sz = y + 22, 100, 80
    s.image(x + 22, row_y + (row_h - ic_sz) / 2, ic_sz, ic_sz, img_b64(os.path.join(HERE, a["icon"])), 18)
    nx, avail = x + 22 + ic_sz + 16, w - 22 - ic_sz - 16 - 14
    size = 48
    while size > 40 and max(text_width(l, "f700", size) for l in wrap(a["name"], "f700", size, avail)) > avail:
        size -= 1
    lines = wrap(a["name"], "f700", size, avail)
    lh = size + 4
    base = row_y + (row_h - len(lines) * lh) / 2 + size * 0.82
    for k, line in enumerate(lines):
        s.text(nx, base + k * lh, line, "f700", size)
    status = a.get("status_phone", a["status"])
    psize = fit_size(status, "m500", 32, w - 44 - 28, 24)
    s.chip(x + 22, row_y + row_h + 16, status, "go", "m500", psize, psize + 12, 14, 1.5, 12, 0, "#062b16")
    return s


def showcase_phone(t, item):
    size, maxw = 30, 264 - 24
    lines = wrap(item["title"], "f600", size, maxw)
    if len(lines) > 2:
        lines = lines[:2]
        while lines[1] and text_width(lines[1] + "...", "f600", size) > maxw:
            lines[1] = lines[1].rsplit(" ", 1)[0] if " " in lines[1] else lines[1][:-1]
        lines[1] += "..."
    for k, line in enumerate(lines):
        while text_width(line, "f600", size) > maxw:
            line = line[:-4] + "..."
        lines[k] = line
    s = Svg(292, 280, t, f"{item['title']} - {item['caption']}")
    s.board(stroke=False)
    x, y, w, h = 14, 14, 264, 252
    s.card(x, y, w, h, "card", 16)
    s.image(x + 12, y + 12, w - 24, 135, img_b64(os.path.join(HERE, item["image"])), 10)
    arrow(s, x + w - 48, y + 108, 28)
    for k, line in enumerate(lines):
        s.text(x + 12, y + 147 + 14 + 26 + k * 36, line, "f600", size)
    return s


def label_phone(t, title, fill):
    s = Svg(440, 80, t, title)
    w = text_width(title, "f700", 38) + 40
    s.add(f'<g transform="rotate(-1.2 {12 + w / 2} 40)">')
    s.rect(16, 16, w, 54, "line", 14)
    s.rect(12, 12, w, 54, fill, 14, "line", 2)
    s.text(32, 52, title, "f700", 38)
    s.add("</g>")
    return s
