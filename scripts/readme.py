# Renders README.md with dark + phone responsive <picture> elements and rich alt text.
from datetime import date
from html import escape

from board import board_label
from cards import app_fact, app_label, fmt, hero_label, whoami_label
from graphs import graph_titles, last_days, title_of, total_of


def line_title(data, today):
    return title_of(total_of(last_days(data, today)), "in the last 30 days")


def picture(name, width, alt, phone=False):
    a = f"assets/{name}"
    srcs = []
    if phone:
        srcs.append(f'<source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="{a}-phone-dark.svg">')
        srcs.append(f'<source media="(max-width: 600px)" srcset="{a}-phone-light.svg">')
    srcs.append(f'<source media="(prefers-color-scheme: dark)" srcset="{a}-dark.svg">')
    attr = f'height="{width[1:]}"' if width.startswith("h") else f'width="{width}"'
    return f'<picture>{"".join(srcs)}<img src="{a}-light.svg" {attr} alt="{escape(alt, quote=True)}"></picture>'


def link(url, inner):
    return f'<a href="{url}">{inner}</a>'


def render(data, P):
    L = P["links"]
    out = [link(L["site"]["url"], picture("hero", "100%", hero_label(P), True)), ""]

    badges = []
    for key, name in (("linkedin", "li"), ("jobly", "jobly"), ("email", "mail"), ("site", "site")):
        alt = f"{L[key]['label']} {L[key]['handle']}".strip()
        badges.append(link(L[key]["url"], picture(f"badge-{name}", "h44", alt)))
    out += ['<p align="center">', *badges, "</p>", ""]

    out += [picture("stats", "100%", board_label(data, P), True), ""]

    if P.get("show_graphs") and "contrib" in data:
        today = date.fromisoformat(data["today"])
        for key, summary, total, title in graph_titles(data, today):
            pic = picture(f"graph-{key}", "100%", title, True)
            if summary is None:
                out += [pic, ""]
            else:
                unit = "contribution" if total == 1 else "contributions"
                out += [f"<details><summary>{summary}: {fmt(total)} {unit}</summary>", "", pic, "", "</details>", ""]
        out += [picture("line-30d", "100%", line_title(data, today), True), ""]

    out += [picture("whoami", "100%", whoami_label(data, P), True), ""]

    out += [picture("label-ship", "100%", "What I ship", True), ""]
    apps = []
    for a in P["apps"]:
        alt = app_label(a, app_fact(a, data, P))
        apps.append(link(a["url"], picture(f"app-{a['id']}", "49%", alt, True)))
    out += ['<p align="center">', *apps, "</p>", ""]

    more_items = []
    for m in P["more"]:
        part = link(m["url"], m["name"]) if m.get("url") else m["name"]
        if m.get("note"):
            part += f" ({m['note']})"
        more_items.append(part)
    out += [f'<p align="center"><sub>Also building: {" · ".join(more_items)}</sub></p>', ""]

    sc = P["showcase"]
    out += [picture("label-showcase", "100%", sc["title"], True), ""]
    tiles = [link(item["url"], picture(f"showcase-{item['id']}", "32%", f"{item['title']} - {item['caption']}", True))
             for item in sc["items"]]
    out += ['<p align="center">', *tiles, "</p>", ""]

    out += [f'<p align="center"><sub>Sticker-board layout inspired by {link("https://github.com/ZazaGdev", "ZazaGdev")} '
            f'· refreshed every night by a GitHub Action · {link(L["site"]["url"], P["site_host"])}</sub></p>', ""]
    return "\n".join(out)
