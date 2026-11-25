# Fetches live public GitHub data for the profile (repos, stars, releases, and optionally
# contribution calendars when show_graphs is enabled in profile.json). Needs no secret;
# GITHUB_TOKEN simply lifts the REST rate limit in GitHub Actions.
import json, os, re, ssl, urllib.error, urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "aymenoppa-profile-build (github.com/aymenoppa/aymenoppa)"


def _ssl_context():
    for ca in (os.environ.get("SSL_CERT_FILE"), "/etc/ssl/cert.pem"):
        if ca and os.path.exists(ca):
            return ssl.create_default_context(cafile=ca)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class SourceError(Exception):
    """One source could not be read or understood."""


class CalendarError(SourceError):
    """The contribution calendar could not be read."""


class Net:
    def __init__(self, token=None):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.ctx = _ssl_context()

    def get(self, url, name="", binary=False):
        headers = {"User-Agent": UA}
        if self.token and url.startswith("https://api.github.com/"):
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30, context=self.ctx) as r:
                data = r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise SourceError(f"{url}: {e}")
        return data if binary else data.decode("utf8")


# ------------------------------------------------------------------ contribution calendar
class _Calendar(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells, self.tips, self.heading = [], {}, []
        self._tip_for, self._tip, self._in_h = None, [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and a.get("data-date"):
            self.cells.append((a["data-date"], a.get("id"), int(a.get("data-level") or 0)))
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for, self._tip = a["for"], []
        elif tag == "h2" and a.get("id") == "js-contribution-activity-description":
            self._in_h = True

    def handle_data(self, data):
        if self._tip_for is not None:
            self._tip.append(data)
        if self._in_h:
            self.heading.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tip_for is not None:
            self.tips[self._tip_for] = " ".join("".join(self._tip).split())
            self._tip_for = None
        elif tag == "h2":
            self._in_h = False


def parse_calendar(html):
    p = _Calendar()
    p.feed(html)
    m = re.search(r"([\d,]+)\s+contributions?", " ".join("".join(p.heading).split()))
    if not m:
        raise CalendarError("contribution heading not found")
    heading = int(m.group(1).replace(",", ""))
    if not p.cells:
        raise CalendarError("no calendar cells found")
    days = []
    for d, cid, level in p.cells:
        tip = p.tips.get(cid)
        if tip is None:
            raise CalendarError(f"no tooltip for {d}")
        t = re.match(r"(No|[\d,]+) contributions? on", tip)
        if not t:
            raise CalendarError(f"unreadable tooltip for {d}: {tip!r}")
        days.append((d, 0 if t.group(1) == "No" else int(t.group(1).replace(",", "")), level))
    if sum(c for _, c, _ in days) != heading:
        raise CalendarError(f"heading says {heading} but the cells add up to {sum(c for _, c, _ in days)}")
    return {"heading": heading, "days": days}


def streaks(days, today):
    iso = lambda d: d.isoformat()
    d = today if days.get(iso(today), 0) > 0 else today - timedelta(days=1)
    cur, start, end = 0, None, d
    while days.get(iso(d), 0) > 0:
        cur += 1
        start = d
        d -= timedelta(days=1)
    best = {"days": 0, "start": None, "end": None}
    run, run_start, prev = 0, None, None
    for k in sorted(k for k, v in days.items() if v > 0 and k <= iso(today)):
        dk = date.fromisoformat(k)
        if prev is not None and dk - prev == timedelta(days=1):
            run += 1
        else:
            run, run_start = 1, dk
        if run >= best["days"]:
            best = {"days": run, "start": iso(run_start), "end": iso(dk)}
        prev = dk
    return ({"days": cur, "start": iso(start) if start else None, "end": iso(end) if start else None}, best)


def fetch_contrib(net, user, created, today, cached_years):
    base = f"https://github.com/users/{user}/contributions"
    last = parse_calendar(net.get(base, "contrib-last-year.html"))
    all_days, years = {}, {}
    for y in range(int(created[:4]), today.year + 1):
        cached = cached_years.get(str(y)) if y < today.year else None
        if cached:
            years[str(y)] = cached
        else:
            cal = parse_calendar(net.get(f"{base}?from={y}-01-01&to={y}-12-31", f"contrib-{y}.html"))
            years[str(y)] = {"total": cal["heading"], "days": {d: c for d, c, _ in cal["days"] if c and d.startswith(str(y))}}
        all_days.update(years[str(y)]["days"])
    for d, c, _ in last["days"]:
        if c:
            all_days[d] = c
        else:
            all_days.pop(d, None)
    iso = today.isoformat()
    all_days = {d: c for d, c in all_days.items() if d <= iso}
    cur, best = streaks(all_days, today)
    cells = sorted(last["days"])
    grid = {"first": cells[0][0], "counts": [c for _, c, _ in cells], "levels": "".join(str(l) for _, _, l in cells)}
    contrib = {
        "last_year": last["heading"],
        "this_year": sum(c for d, c in all_days.items() if d.startswith(str(today.year))),
        "all_time": sum(all_days.values()),
        "since_year": int(created[:4]),
        "current_streak": cur,
        "longest_streak": best,
        "grid": grid,
        "days": all_days,
    }
    return contrib, {k: v for k, v in years.items() if int(k) < today.year}


def fetch_repos(net, user):
    repos, page = [], 1
    while True:
        batch = json.loads(net.get(f"https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}"))
        repos += batch
        if len(batch) < 100 or page >= 5:
            break
        page += 1
    own = [r for r in repos if not r["fork"] and not r["private"]]
    out = {"public_repos": len(own), "stars": sum(r["stargazers_count"] for r in own), "downloads": 0, "repos": {}}
    for r in own:
        out["repos"][r["name"]] = {
            "stars": r["stargazers_count"],
            "downloads": 0,
            "tag": None,
            "description": r.get("description") or "",
            "language": r.get("language") or "",
        }
    return out


STALE_AFTER_DAYS = 3


def stale_sources(good, today, limit=STALE_AFTER_DAYS):
    return [(k, v) for k, v in sorted(good.items()) if (today - date.fromisoformat(v)).days > limit]


def collect(net, profile, today, state=None):
    state = state or {}
    saved = state.get("sources", {})
    user = profile["user"]
    data = {"today": today.isoformat()}
    notes, fresh = [], {}
    years = dict(state.get("years", {}))

    if profile.get("show_graphs"):
        contrib, years = fetch_contrib(net, user, profile["created"], today, years)
        data["contrib"] = contrib
        notes.append(("contrib", f"github.com/users/{user}/contributions"))

    good = {k: v for k, v in state.get("good", {}).items() if k == "repos"}
    try:
        data["repos"] = fetch_repos(net, user)
        fresh["repos"] = data["repos"]
        good["repos"] = today.isoformat()
        notes.append(("repos", f"api.github.com/users/{user}/repos"))
    except (SourceError, KeyError, ValueError, TypeError) as e:
        if "repos" not in saved:
            data["repos"] = {"public_repos": 0, "stars": 0, "downloads": 0, "repos": {}}
            notes.append(("repos", f"empty fallback ({e})"))
        else:
            data["repos"] = saved["repos"]
            notes.append(("repos", f"state.json (live fetch failed: {e})"))

    new_state = {
        "fetched": today.isoformat(),
        "good": good,
        "sources": {**saved, **fresh},
        "years": years,
    }
    return data, new_state, notes
