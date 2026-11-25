# Draws the sticker-board cards (light and dark) from fetched data and profile.json.
# Layout sizes: boards are 880 wide, phone variants 440, app cards 440, showcase tiles 292.
import os
from datetime import date

from svgkit import Svg, HERE, img_b64, mix, text_width, wrap

THEMES = ("light", "dark")


def fmt(n):
    return f"{n:,}"


def short_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')}"


def long_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def fit_size(text, font, size, maxw, floor):
    while size > floor and text_width(text, font, size) > maxw:
        size -= 1
    return size


def sticker_link(s, x, y, w, h, label, size, rot=5):
    cx, cy = x + w / 2, y + h / 2
    s.add(f'<g transform="rotate({rot} {cx} {cy})">')
    s.rect(x + 4, y + 4, w, h, "line", 10)
    s.rect(x, y, w, h, "pop", 10, "line", 2)
    s.text(cx, cy + size * 0.36, label, "f700", size, "on-pop", "middle")
    s.add("</g>")


def name_line(s, x, base, name, size):
    """'Hi, I'm <Name>' with the name on a coral-pink highlight."""
    lead = "Hi, I'm "
    w1 = text_width(lead, "f700", size)
    wn = text_width(name, "f700", size)
    s.rect(x + w1 - size * 0.14, base - size * 0.93, wn + size * 0.28, size * 1.2, "yt", size * 0.2)
    s.text(x, base, lead + name, "f700", size)


def hero_label(P):
    return f"Hi, I'm {P['name']}. {P['tagline']}"


# ---------------------------------------------------------------- hero
def hero(t, data, P):
    s = Svg(880, 244, t, hero_label(P))
    s.board()
    s.alogo(40, 42, 104)
    x0 = 172
    name_line(s, x0, 106, P["name"], 58)
    tag = P["tagline"]
    s.text(x0, 150, tag, "f500", fit_size(tag, "f500", 21, 880 - x0 - 40, 17), "muted")
    cx = x0
    for label, fill in P["tags"]:
        cx += s.chip(cx, 170, label, fill, "f600", 15, 32, 13, 2, 9, 3) + 14
    host = P["site_host"]
    sw = max(126, int(text_width(host, "f700", 18) + 28))
    sticker_link(s, 850 - sw, 32, sw, 44, host, 18)
    return s


# ---------------------------------------------------------------- badges
def badge(t, label, handle, fill, icon=None):
    w = 26 + (30 if icon else 0) + text_width(label, "f600", 17) + (10 + text_width(handle, "m400", 15) if handle else 0) + 10
    s = Svg(int(w) + 8, 46, t, f"{label} {handle}".strip())
    s.rect(4, 7, w - 4, 36, "line", 10)
    s.rect(1, 3, w - 4, 36, fill, 10, "line", 2)
    x = 15
    if icon == "star":
        s.rect(x, 11, 22, 20, "card", 5, "line", 1.5)
        s.add(f'<path d="M{x + 11} 14.5 L{x + 12.7} 18.2 L{x + 16.8} 18.7 L{x + 13.8} 21.4 L{x + 14.6} 25.4 '
              f'L{x + 11} 23.4 L{x + 7.4} 25.4 L{x + 8.2} 21.4 L{x + 5.2} 18.7 L{x + 9.3} 18.2 Z" fill="{s.col("pop")}"/>')
        x += 30
    x += s.text(x, 27, label, "f600", 17) + 10
    if handle:
        s.text(x, 26, handle, "m400", 15)
    return s


# ---------------------------------------------------------------- whoami terminal
def terminal_rows(lines, size, maxw):
    rows = []
    for line in lines:
        plain = "".join(t for t, _, _ in line) if line else ""
        if line is None or text_width(plain, "m400", size) <= maxw:
            rows.append(line)
        elif len(line) == 1:
            rows += [[(part, line[0][1], line[0][2])] for part in wrap(plain, "m400", size, maxw)]
        elif len(line) == 2:
            (p, pf, pfont), (t, tf, tfont) = line
            parts = wrap(t, "m400", size, maxw - text_width(p, "m400", size))
            rows.append([(p, pf, pfont), (parts[0], tf, tfont)])
            rows += [[(" " * len(p), tf, None), (part, tf, tfont)] for part in parts[1:]]
        else:
            rows.append(line)
    return rows


def terminal_height(lines, size, lh, w, pad=24):
    rows = terminal_rows(lines, size, w - pad * 2)
    return int(38 + pad + size * 0.7 + sum(lh * 0.45 if r is None else lh for r in rows) - lh * 0.2 + pad)


def _terminal(s, x, y, w, h, title, lines, size, lh, pad=24):
    s.rect(x + 4, y + 4, w, h, "line", 14)
    s.rect(x, y, w, h, "screen", 14, "line", 2)
    s.add(f'<line x1="{x}" y1="{y + 38}" x2="{x + w}" y2="{y + 38}" stroke="{s.col("line")}" stroke-width="2"/>')
    for i, c in enumerate(("pop", "rd", "go")):
        s.add(f'<circle cx="{x + 22 + i * 20}" cy="{y + 19}" r="6" fill="{s.col(c)}" stroke="{s.col("line")}" stroke-width="1.5"/>')
    s.text(x + w / 2, y + 25, title, "m400", 15, "on-screen-muted", "middle")
    ly = y + 38 + pad + size * 0.7
    maxw = w - pad * 2
    for line in terminal_rows(lines, size, maxw):
        if line is None:
            ly += lh * 0.45
            continue
        s.tspans(x + pad, ly, line, "m400", size)
        ly += lh
    cx = x + pad + text_width("$ ", "m500", size)
    s.rect(cx, ly - lh - size * 0.8, size * 0.55, size * 1.05, "on-screen", 1, extra='class="cur"')
    s.css.append("@keyframes blink{50%{opacity:0}}.cur{animation:blink 1.1s steps(1) infinite}"
                 "@media (prefers-reduced-motion:reduce){.cur{animation:none}}")


def whoami_lines(data, P, phone=False):
    w = P["whoami"]
    who = ([[(P["name"].lower(), "on-screen", "m500"), (f"  ·  {P['role']}", "on-screen-muted", None)],
            [(P["location"], "on-screen-muted", None)]] if phone else
           [[(P["name"].lower(), "on-screen", "m500"), (f"  ·  {P['role']}  ·  {P['location']}", "on-screen-muted", None)]])
    L = [
        [("$ ", "pop", "m500"), ("whoami", "on-screen", "m500")],
        *who,
        [(w["bio"], "on-screen-muted", None)],
        None,
        [("$ ", "pop", "m500"), ("cat stack.txt", "on-screen", "m500")],
        [(w["stack"], "on-screen-muted", None)],
        None,
        [("$ ", "pop", "m500"), ("cat now.txt", "on-screen", "m500")],
    ]
    L += [[("→ ", "go", None), (n, "on-screen-muted", None)] for n in w["now"]]
    return L


def whoami_label(data, P):
    w = P["whoami"]
    return (f"whoami: {P['name'].lower()}, {P['role']}, {P['location']}. {w['bio']} "
            f"Stack: {w['stack']}. Now: " + ". ".join(w["now"]) + ".")


def whoami(t, data, P):
    L = whoami_lines(data, P)
    L += [[("$ ", "pop", "m500")]]
    h = terminal_height(L, 18, 29, 826)
    s = Svg(880, h + 44, t, whoami_label(data, P))
    s.board()
    _terminal(s, 24, 22, 826, h, P["terminal_title"], L, 18, 29)
    return s


# ---------------------------------------------------------------- section labels
def label(t, title, chip, fill, chip_fill):
    s = Svg(880, 66, t, title)
    w = text_width(title, "f700", 28) + 36
    s.add(f'<g transform="rotate(-1.2 {12 + w / 2} 33)">')
    s.rect(16, 14, w, 44, "line", 12)
    s.rect(12, 10, w, 44, fill, 12, "line", 2)
    s.text(30, 42, title, "f700", 28)
    s.add("</g>")
    if chip:
        s.chip(w + 36, 20, chip, chip_fill, "m500", 15, 30, 11)
    return s


# ---------------------------------------------------------------- app cards
def arrow(s, x, y, size=30):
    s.rect(x + 2, y + 2, size, size, "line", 8)
    s.rect(x, y, size, size, "pop", 8, "line", 2)
    c = s.col("on-pop")
    m = size * 0.3
    e = size - m
    s.add(f'<path d="M{x + m:.1f} {y + e:.1f} L{x + e:.1f} {y + m:.1f} M{x + m + 2:.1f} {y + m:.1f} H{x + e:.1f} V{y + e - 2:.1f}" '
          f'stroke="{c}" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def app_fact(a, data, P):
    repo = data["repos"]["repos"].get(a.get("repo", ""), {})
    parts = []
    for key in a["fact"]:
        if key == "stars":
            stars = repo.get("stars")
            if stars:
                parts.append(f"{fmt(stars)} star" if stars == 1 else f"{fmt(stars)} stars")
        elif key == "tag":
            if repo.get("tag"):
                parts.append(repo["tag"])
        else:
            parts.append(key)
    return parts


def app_label(a, parts):
    return f"{a['name']}: {a['line']} {a['status'].capitalize()}, {', '.join(parts)}."


def app(t, a, data, P):
    parts = app_fact(a, data, P)
    s = Svg(440, 304, t, app_label(a, parts))
    s.board(stroke=False)
    x, y, w, h = 16, 16, 408, 274
    s.card(x, y, w, h, mix(s.col(a["tint"]), s.col("card"), 0.38))
    s.image(x + 20, y + 24, 72, 72, img_b64(os.path.join(HERE, a["icon"])), 16)
    nx = x + 108
    size = fit_size(a["name"], "f700", 28, w - 108 - 54, 24)
    s.text(nx, y + 66, a["name"], "f700", size)
    s.chip(nx, y + 76, a["status"], "go", "m500", 13, 24, 10, 1.5, 12, 0, "#062b16")
    arrow(s, x + w - 46, y + 14, 28)
    lines = wrap(a["line"], "f500", 19, w - 40)
    if len(lines) > 2:
        raise ValueError(f"{a['name']}: description needs {len(lines)} lines, shorten it")
    ly = y + 134
    for line in lines:
        s.text(x + 20, ly, line, "f500", 19)
        ly += 26
    cx = x + 20
    for lab, fill in a["chips"]:
        cx += s.chip(cx, y + 186, lab, fill, "m500", 13, 26, 9) + 8
    text = "  ·  ".join(parts)
    while len(parts) > 1 and text_width(text, "m400", 15) > w - 40:
        parts = parts[:-1]
        text = "  ·  ".join(parts)
    s.text(x + 20, y + 246, text, "m400", 15, "muted")
    return s


# ---------------------------------------------------------------- showcase tiles (3-col row)
def showcase(t, item):
    s = Svg(292, 296, t, f"{item['title']} - {item['caption']}")
    s.board(stroke=False)
    x, y, w, h = 14, 14, 264, 268
    s.card(x, y, w, h, "card", 16)
    s.image(x + 12, y + 12, w - 24, 135, img_b64(os.path.join(HERE, item["image"])), 10)
    arrow(s, x + w - 48, y + 108, 28)
    lines = wrap(item["title"], "f600", 18, w - 24)
    if len(lines) > 2:
        lines = lines[:2]
        while text_width(lines[1] + "...", "f600", 18) > w - 24:
            lines[1] = lines[1].rsplit(" ", 1)[0]
        lines[1] += "..."
    ly = y + 176
    for line in lines:
        s.text(x + 12, ly, line, "f600", 18)
        ly += 23
    s.text(x + 12, y + h - 16, item["caption"], "m400", 13, "muted")
    return s
