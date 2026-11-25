# Entry point. `python3 scripts/build.py` fetches live public GitHub data, draws every SVG
# (light + dark, desktop + phone) into assets/ and writes README.md.
import json, os, sys
from datetime import date, datetime, timezone

import board, cards, fetch, graphs, phone, readme
from svgkit import HERE as SCRIPTS

ROOT = os.path.dirname(SCRIPTS)
THEMES = cards.THEMES
KB_LIMIT = 150


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf8") as f:
        return json.load(f)


def make_assets(data, P):
    out = {}
    for t in THEMES:
        out[f"hero-{t}.svg"] = cards.hero(t, data, P)
        out[f"hero-phone-{t}.svg"] = phone.hero_phone(t, data, P)
        out[f"stats-{t}.svg"] = board.stats_board(t, data, P)
        out[f"stats-phone-{t}.svg"] = phone.stats_board_phone(t, data, P)
        if P.get("show_graphs") and "contrib" in data:
            out.update(graphs.make_graphs(t, data, date.fromisoformat(data["today"]))[0])
        out[f"whoami-{t}.svg"] = cards.whoami(t, data, P)
        out[f"whoami-phone-{t}.svg"] = phone.whoami_phone(t, data, P)
        out[f"label-ship-{t}.svg"] = cards.label(t, "What I ship", f"{len(P['apps'])} flagship apps", "rd", "card")
        out[f"label-ship-phone-{t}.svg"] = phone.label_phone(t, "What I ship", "rd")
        sc = P["showcase"]
        out[f"label-showcase-{t}.svg"] = cards.label(t, sc["title"], sc["chip"], "yt", "card")
        out[f"label-showcase-phone-{t}.svg"] = phone.label_phone(t, sc["title"], "yt")
        for key, name, fill, ic in (("linkedin", "li", "lx", None),
                                    ("jobly", "jobly", "li", "star"),
                                    ("email", "mail", "rd", None),
                                    ("site", "site", "card", None)):
            L = P["links"][key]
            out[f"badge-{name}-{t}.svg"] = cards.badge(t, L["label"], L["handle"], fill, ic)
        for a in P["apps"]:
            out[f"app-{a['id']}-{t}.svg"] = cards.app(t, a, data, P)
            out[f"app-{a['id']}-phone-{t}.svg"] = phone.app_phone(t, a, data, P)
        for item in sc["items"]:
            out[f"showcase-{item['id']}-{t}.svg"] = cards.showcase(t, item)
            out[f"showcase-{item['id']}-phone-{t}.svg"] = phone.showcase_phone(t, item)
    return out


def run(out_root=ROOT, state_path=None, today=None, log=print):
    P = load_json(os.path.join(ROOT, "profile.json"))
    state_path = state_path or os.path.join(SCRIPTS, "state.json")
    state = load_json(state_path)
    net = fetch.Net()
    today = today or datetime.now(timezone.utc).date()
    data, new_state, notes = fetch.collect(net, P, today, state)
    svgs = make_assets(data, P)
    files, warnings = {}, []
    for name, s in svgs.items():
        rendered = s.render()
        files[f"assets/{name}"] = rendered
        if s.overflow:
            warnings.append(f"{name}: text runs past the edge: {s.overflow}")
        kb = len(rendered.encode("utf8")) / 1024
        if kb > KB_LIMIT:
            warnings.append(f"{name}: {kb:.1f} KB is over {KB_LIMIT} KB")
    files["README.md"] = readme.render(data, P)

    assets_dir = os.path.join(out_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    for old in os.listdir(assets_dir):
        if old.endswith(".svg") and f"assets/{old}" not in files:
            os.remove(os.path.join(assets_dir, old))
    for rel, text in files.items():
        with open(os.path.join(out_root, rel), "w", encoding="utf8", newline="\n") as f:
            f.write(text if rel != "README.md" else text.rstrip("\n") + "\n")
    with open(state_path, "w", encoding="utf8", newline="\n") as f:
        json.dump(new_state, f, indent=1, ensure_ascii=False)
        f.write("\n")

    log(f"built {len(svgs)} SVGs for {today.isoformat()}")
    for what, where in notes:
        log(f"  source {what}: {where}")
    max_kb = max(len(v.encode("utf8")) / 1024 for k, v in files.items() if k.endswith(".svg"))
    log(f"  largest SVG: {max_kb:.1f} KB (limit {KB_LIMIT} KB)")
    for w in warnings:
        log(f"  WARNING {w}")
    return {"data": data, "files": files, "warnings": warnings}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    res = run()
    return 1 if res["warnings"] else 0


if __name__ == "__main__":
    sys.exit(main())
