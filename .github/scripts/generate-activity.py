from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import os
import html

USERNAME = "hussainasadullah496-ux"
OUT = Path("dist/github-activity.svg")
OUT.parent.mkdir(parents=True, exist_ok=True)

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=83)
weekly = [0] * 12
token = os.environ.get("GITHUB_TOKEN", "")
headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "profile-readme-activity-generator",
}
if token:
    headers["Authorization"] = f"Bearer {token}"

try:
    request = Request(
        f"https://api.github.com/users/{USERNAME}/events/public?per_page=100",
        headers=headers,
    )
    with urlopen(request, timeout=20) as response:
        events = json.loads(response.read().decode("utf-8"))
    counts = Counter()
    for event in events:
        day = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")).date()
        if start <= day <= today:
            counts[day] += 1
    for day, count in counts.items():
        week_index = min(11, max(0, (day - start).days // 7))
        weekly[week_index] += count
except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
    print(f"Could not fetch recent public GitHub events: {exc}")
    weekly = [0] * 12

width, height = 1000, 270
left, right, top, bottom = 52, 24, 48, 48
plot_w, plot_h = width - left - right, height - top - bottom
max_value = max(weekly) or 1
gap = 14
bar_w = (plot_w - gap * 11) / 12
bars = []
for i, value in enumerate(weekly):
    bar_h = max(3, (value / max_value) * (plot_h - 14)) if value else 3
    x = left + i * (bar_w + gap)
    y = top + plot_h - bar_h
    label = (start + timedelta(days=i * 7)).strftime("%b %d")
    bars.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="5" fill="#8b5cf6" opacity=".9"/>'
        f'<text x="{x + bar_w/2:.1f}" y="{top + plot_h + 22}" text-anchor="middle" fill="#a5b4fc" font-size="12">{html.escape(label)}</text>'
        f'<text x="{x + bar_w/2:.1f}" y="{max(top + 13, y - 7):.1f}" text-anchor="middle" fill="#e5e7eb" font-size="12">{value}</text>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Recent public GitHub activity</title>
<desc id="desc">Weekly counts of public GitHub events observed in the last 84 days. This is not a complete count of commits or private contributions.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#111827"/><stop offset="100%" stop-color="#0d1117"/></linearGradient></defs>
<rect width="100%" height="100%" rx="12" fill="url(#bg)" stroke="#30363d"/>
<text x="{left}" y="28" fill="#c4b5fd" font-size="19" font-family="Segoe UI,Arial,sans-serif" font-weight="700">PUBLIC GITHUB ACTIVITY · LAST 12 WEEKS</text>
<line x1="{left}" y1="{top + plot_h}" x2="{width-right}" y2="{top+plot_h}" stroke="#374151"/>
{''.join(bars)}
<text x="{left}" y="{height-10}" fill="#9ca3af" font-size="11" font-family="Segoe UI,Arial,sans-serif">Based on GitHub public-event API data; may omit events beyond its API window.</text>
</svg>
'''
OUT.write_text(svg, encoding="utf-8")
print(f"Wrote {OUT}")
