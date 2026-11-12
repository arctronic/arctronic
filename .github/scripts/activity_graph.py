#!/usr/bin/env python3
"""Render a contribution activity graph SVG (radical theme) from the GitHub GraphQL API.

Usage: GH_TOKEN=... python activity_graph.py <username> <output.svg> [days]
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""

# radical theme
BG, TITLE, LINE, POINT, AXIS, GRID, AREA = (
    "#141321", "#fe428e", "#fe428e", "#a9fef7", "#a9fef7", "#2a2a40", "#fe428e")


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "activity-graph"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    user = data["data"]["user"]
    days = [d for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    return user["name"] or login, days


def render(name, days):
    W, H = 1200, 420
    L, R, T, B = 70, 30, 70, 70
    pw, ph = W - L - R, H - T - B
    counts = [d["contributionCount"] for d in days]
    top = max(counts) or 1
    step = max(1, -(-top // 5))  # ceil(top/5)
    ymax = step * 5
    n = len(days)
    x = lambda i: L + pw * i / (n - 1 if n > 1 else 1)
    y = lambda v: T + ph - ph * v / ymax
    pts = [(x(i), y(c)) for i, c in enumerate(counts)]

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>',
           f'<text x="{W/2}" y="40" text-anchor="middle" font-size="22" font-weight="600" '
           f'fill="{TITLE}">{escape(name)}\'s Contribution Graph</text>']
    for k in range(6):
        v = step * k
        yy = y(v)
        out.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{L-10}" y="{yy+4:.1f}" text-anchor="end" font-size="12" fill="{AXIS}">{v}</text>')
    for i, d in enumerate(days):
        if i % 2 == 0 or n <= 16:
            day = dt.date.fromisoformat(d["date"]).day
            out.append(f'<text x="{x(i):.1f}" y="{T+ph+20}" text-anchor="middle" font-size="12" '
                       f'fill="{AXIS}">{day}</text>')
    out.append(f'<text x="{W/2}" y="{H-15}" text-anchor="middle" font-size="13" fill="{AXIS}">Days</text>')
    out.append(f'<text x="20" y="{T+ph/2}" text-anchor="middle" font-size="13" fill="{AXIS}" '
               f'transform="rotate(-90 20 {T+ph/2})">Contributions</text>')
    poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    out.append(f'<polygon points="{L},{T+ph} {poly} {W-R},{T+ph}" fill="{AREA}" fill-opacity="0.12"/>')
    out.append(f'<polyline points="{poly}" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>')
    for (px, py), d in zip(pts, days):
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{POINT}">'
                   f'<title>{d["date"]}: {d["contributionCount"]}</title></circle>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    login, path = sys.argv[1], sys.argv[2]
    ndays = int(sys.argv[3]) if len(sys.argv) > 3 else 31
    token = os.environ.get("GH_TOKEN") or sys.exit("GH_TOKEN is not set")
    name, days = fetch(login, token)
    today = dt.date.today().isoformat()
    days = [d for d in days if d["date"] <= today][-ndays:]
    with open(path, "w") as f:
        f.write(render(name, days))


if __name__ == "__main__":
    main()
