"""
Generates an animated GitHub-green contribution heatmap as a static SVG.
Reads the same public contribution data GitHub itself shows on your profile
(https://github.com/users/<username>/contributions) - no API token needed.
The heatmap draws itself in column by column, and active days pulse gently.
"""
import urllib.request
import re
import datetime
import sys

USERNAME = "LeandroCell"
OUT_PATH = "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]  # standard GitHub dark-theme green
CELL = 11
GAP = 3
TOTAL_REVEAL = 1.4  # seconds for the whole grid to draw in


def fetch(username):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse(html_text):
    pattern = re.compile(r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"')
    return [
        (datetime.date.fromisoformat(m.group(1)), int(m.group(2)))
        for m in pattern.finditer(html_text)
    ]


def build_grid(days):
    days = sorted(days, key=lambda x: x[0])
    start = days[0][0]
    grid = {}
    max_col = 0
    for d, lvl in days:
        delta = (d - start).days
        col = delta // 7
        row = (d.weekday() + 1) % 7  # Sunday = 0
        grid[(row, col)] = lvl
        max_col = max(max_col, col)
    return grid, max_col + 1


def render_svg(grid, cols, out_path):
    rows = 7
    width = cols * (CELL + GAP) + GAP
    height = rows * (CELL + GAP) + GAP
    step = TOTAL_REVEAL / cols

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">']
    for (row, col), lvl in grid.items():
        x = GAP + col * (CELL + GAP)
        y = GAP + row * (CELL + GAP)
        color = PALETTE[lvl] if lvl < len(PALETTE) else PALETTE[-1]
        delay = col * step
        parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" opacity="0">')
        parts.append(f'<animate attributeName="opacity" from="0" to="1" dur="0.12s" begin="{delay:.2f}s" fill="freeze"/>')
        if lvl > 0:
            pulse_begin = TOTAL_REVEAL + (col % 5) * 0.15
            parts.append(f'<animate attributeName="opacity" values="1;0.55;1" dur="2.2s" begin="{pulse_begin:.2f}s" repeatCount="indefinite"/>')
        parts.append("</rect>")
    parts.append("</svg>")
    with open(out_path, "w") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    html_text = fetch(username)
    days = parse(html_text)
    if not days:
        raise SystemExit("No contribution data parsed - GitHub markup may have changed.")
    grid, cols = build_grid(days)
    render_svg(grid, cols, OUT_PATH)
    print(f"Wrote {OUT_PATH} ({cols} weeks, {len(days)} days)")
