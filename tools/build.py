#!/usr/bin/env python3
"""Build the SYN-OS desktop that is the syn990 profile.

Every picture the README and its pages show is an SVG tile drawn here from
Terminus bitmaps (tools/font), desktop.toml and GitHub's own numbers:

  GH_TOKEN=$(gh auth token) python3 tools/build.py
  python3 tools/build.py --sync     # after changing the notice's link

writes var/desktop/*.svg (the README), var/chrome/*.svg (each page's title
bar) and var/folders/*.svg (the folder views). The pages load them by
relative path, so they show in any Markdown preview as well as on GitHub.
The workflow reruns it every morning and commits whatever changed: the date
in the bar and syn-sysmon's numbers. The README lays the tiles edge to edge, each
one a link, so the desktop reads as one picture whose parts open. Standard
library only, so it runs as-is on a runner.
"""
import base64
import datetime
import json
import math
import os
import random
import shutil
import sys
import tomllib
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
FONT = json.loads((ROOT / "tools/font/terminus.json").read_text(encoding="utf-8"))
CONF = tomllib.loads((ROOT / "desktop.toml").read_text(encoding="utf-8"))
LOGIN = "syn990"
SINCE = 2017

W = 1000
BG = "#060606"
RED = "#ff2a2a"
DARK = "#5a0a0a"
DIM = "#8a2020"
TEAL = "#00e5c7"
TEXT = "#e4e4e4"
GREY = "#8a8a8a"
WIN = "#0a0a0a"
EDGE = "#3a0b0b"

# Bands of the README desktop: (top, height). Every band is at least 80 tall,
# so on a phone each row of tiles stays taller than a line of text and no gap
# opens between rows.
BAR = 40
BAND_A = (0, 150)
BAND_B = (150, 340)
BAND_C = (490, 300)
ICON_W = 94
ICONS_N = 7

CSS = """
.fi{animation:fi .5s both}
@keyframes fi{from{opacity:0}to{opacity:1}}
.blink{animation:blink 1.06s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.toast{animation:toast .7s cubic-bezier(.2,.9,.3,1) 1s both}
@keyframes toast{from{transform:translateX(360px)}to{transform:none}}
.pulse{opacity:0;animation:pulse 2.4s ease-in-out 1.8s infinite}
@keyframes pulse{50%{opacity:1}}
.grow{transform-box:fill-box;transform-origin:50% 100%;animation:grow .5s cubic-bezier(.2,.8,.3,1) both}
@keyframes grow{from{transform:scaleY(0)}}
.bar{transform-box:fill-box;transform-origin:0 50%;animation:bar .9s cubic-bezier(.2,.8,.3,1) both}
@keyframes bar{from{transform:scaleX(0)}}
.slide{opacity:0;animation:slide 16s infinite both}
.slide.first{opacity:1}
.glitch{animation:glitch .9s steps(1) 1.1s both}
@keyframes glitch{0%{opacity:0}10%{opacity:1;transform:translateX(-6px)}20%{opacity:.3;transform:translateX(4px)}30%{opacity:1;transform:translateX(-2px)}40%{opacity:.6;transform:none}50%,100%{opacity:1}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# Text: Terminus glyphs as runs of lit pixels.

def runs(s, x, y, face, scale, track):
    f = FONT[face]
    gw, glyphs = f["w"], f["glyphs"]
    step = gw * scale + track
    d = []
    for i, ch in enumerate(s):
        ox = x + i * step
        for r, bits in enumerate(glyphs.get(ch, glyphs["?"])):
            c = 0
            while c < gw:
                if bits >> (gw - 1 - c) & 1:
                    a = c
                    while c < gw and bits >> (gw - 1 - c) & 1:
                        c += 1
                    k = (c - a) * scale
                    d.append(f"M{n(ox + a * scale)} {n(y + r * scale)}h{n(k)}v{n(scale)}h{n(-k)}z")
                else:
                    c += 1
    return "".join(d)


def width(s, face="ter-u14n", scale=1, track=0):
    return len(s) * (FONT[face]["w"] * scale + track) - (track if s else 0)


def ink(face):
    rows = [r for r, b in enumerate(FONT[face]["glyphs"]["H"]) if b]
    return rows[0], rows[-1] + 1


def text(s, x, y, fill, face="ter-u14n", scale=1, track=0, anchor="start", mid=False, cls="", style=""):
    """s at x, with y the top of the cell, or with mid=True the middle of its capitals."""
    if anchor != "start":
        x -= width(s, face, scale, track) / (2 if anchor == "middle" else 1)
    if mid:
        t, b = ink(face)
        y -= (t + b) / 2 * scale
    attrs = (f' class="{cls}"' if cls else "") + (f' style="{style}"' if style else "")
    return f'<path{attrs} fill="{fill}" d="{runs(s, x, y, face, scale, track)}"/>'


def wrap(s, cols, lines):
    out, line = [], ""
    for word in s.split():
        if line and len(line) + 1 + len(word) > cols:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    out.append(line)
    if len(out) > lines:
        print(f"warning: {s[:40]!r}... is longer than {lines} lines of {cols}", file=sys.stderr)
        out = out[:lines]
        out[-1] = out[-1][:cols - 1] + "…"
    return out


# Icons: 16x16 pixel art, drawn three times over.

PAL = {"#": RED, "+": DARK, "o": "#a01414", "w": TEXT, "g": "#9a9a9a", "k": "#0c0c0c",
       "t": TEAL, "y": "#ffcc33", "G": "#3cff3c", "c": "#22d3ff", "r": "#ff3b3b", "e": "#5f8f8a"}


def _folder(emblem=()):
    rows = ["................", ".######.........", "#++++++#........", "#+++++++#######.",
            "#++++++++++++++#", "################"] + ["#oooooooooooooo#"] * 7 + ["################", "................", "................"]
    rows = [list(r) for r in rows]
    for x, y in emblem:
        rows[y][x] = "w"
    return ["".join(r) for r in rows]


_CIRCLE = [".....######.....", "...##......##...", "..#..........#..", ".#............#.",
           ".#............#.", "#..............#", "#..............#", "#..............#",
           "#..............#", "#..............#", "#..............#", ".#............#.",
           ".#............#.", "..#..........#..", "...##......##...", ".....######....."]


def _round(fill, rim="#"):
    rows = []
    for y, mask in enumerate(_CIRCLE):
        a, b = mask.index("#"), mask.rindex("#")
        rows.append("".join(rim if ch == "#" else fill(x, y, math.hypot(x - 7.5, y - 7.5)) if a < x < b else "."
                            for x, ch in enumerate(mask)))
    return rows


def _disc(x, y, r):
    if r < 1.5:
        return "."
    if r < 2.6:
        return "g"
    a = math.degrees(math.atan2(y - 7.5, x - 7.5))
    return "w" if 3.4 < r < 5.4 and -165 < a < -115 else "+" if r > 6 else "o"


_DISH = {(5, 4): "G", (5, 5): "G", (4, 6): "G", (6, 6): "G", (5, 7): "G", (10, 4): "r", (10, 5): "r",
         (11, 6): "r", (3, 9): "c", (4, 10): "c", (4, 11): "c", (11, 10): "c", (12, 9): "c",
         (8, 9): "w", (7, 10): "w", (8, 10): "w", (9, 10): "w", (8, 11): "w", (11, 12): "G", (12, 12): "G"}

ICONS = {
    "folder": _folder(),
    "bin": _folder([(3, 7), (4, 8), (3, 9), (6, 10), (7, 10), (8, 10)]),
    "doc": ["..#########.....", "..#wwwwwww##....", "..#wwwwwww#w#...", "..#wwwwwww#ww#..",
            "..#wwwwwww####..", "..#wgggggwwww#..", "..#wwwwwwwwww#..", "..#wggggggggw#..",
            "..#wwwwwwwwww#..", "..#wgggggggww#..", "..#wwwwwwwwww#..", "..#wggggggggw#..",
            "..#wwwwwwwwww#..", "..#wggggwwwww#..", "..#wwwwwwwwww#..", "..############.."],
    "picture": ["................", "################", "#kkkkkkkkkkkkkk#", "#kkkkkkkkkkyykk#",
                "#kkkkkkkkkyyyyk#", "#kkkkkkkkkkyykk#", "#kkkkkkkkkkkkkk#", "#kkkkkttkkkkkkk#",
                "#kkkkttttkkkkkk#", "#kkkttttttkk+kk#", "#kktttttttt+++k#", "#kttttttttt++++#",
                "#tttttttttt++++#", "#tttttttttt++++#", "################", "................"],
    "exec": ["................", "................", "################", "#oooooooooooooo#",
             "################", "#kkkkkkkkkkkkkk#", "#ktkkkkkkkkkkkk#", "#kktkkkkkkkkkkk#",
             "#kkktkkkkkkkkkk#", "#kktkkkkkkkkkkk#", "#ktkkktttttkkkk#", "#kkkkkkkkkkkkkk#",
             "#kkkkkkkkkkkkkk#", "################", "................", "................"],
    "mail": ["................", "................", "################", "#w++++++++++++w#",
             "#+w++++++++++w+#", "#++w++++++++w++#", "#+++w++++++w+++#", "#++++w++++w++++#",
             "#+++++wwww+++++#", "#++++++++++++++#", "#++++++++++++++#", "#++++++++++++++#",
             "################", "................", "................", "................"],
    "play": ["................", "................", "................", ".##############.",
             "################", "######ww########", "######www#######", "######wwww######",
             "######wwwww#####", "######wwww######", "######www#######", "######ww########",
             "################", ".##############.", "................", "................"],
    "disc": _round(_disc),
    "dish": _round(lambda x, y, r: _DISH.get((x, y), "k"), rim="e"),
}
ICONS["log"] = [r.replace("g", "o") for r in ICONS["doc"]]
for _name, _rows in ICONS.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), _name


def icon(name, x, y, s=3, cls="", style=""):
    by = {}
    for r, row in enumerate(ICONS[name]):
        c = 0
        while c < 16:
            ch = row[c]
            if ch == ".":
                c += 1
                continue
            a = c
            while c < 16 and row[c] == ch:
                c += 1
            by.setdefault(ch, []).append(f"M{n(x + a * s)} {n(y + r * s)}h{n((c - a) * s)}v{n(s)}h{n(-(c - a) * s)}z")
    attrs = (f' class="{cls}"' if cls else "") + (f' style="{style}"' if style else "")
    return f"<g{attrs}>" + "".join(f'<path fill="{PAL[ch]}" d="{"".join(p)}"/>' for ch, p in by.items()) + "</g>"


# Scenery shared by every tile, in absolute coordinates so it lines up across tiles.

DEFS = f"""<defs>
<radialGradient id="glow" cx="500" cy="420" r="620" gradientUnits="userSpaceOnUse">
<stop offset="0" stop-color="#ff1a1a" stop-opacity=".09"/><stop offset="1" stop-color="#ff1a1a" stop-opacity="0"/></radialGradient>
<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity=".22"/></pattern>
<linearGradient id="barfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff4a4a"/><stop offset="1" stop-color="#8a0000"/></linearGradient>
</defs>"""


def _density(x, y):
    """Value noise on a coarse grid: where the wallpaper's grime clusters."""
    g = 170
    gx, gy = x / g, y / g
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0

    def v(i, j):
        return random.Random(i * 92821 + j * 68903).random()
    top = v(x0, y0) * (1 - fx) + v(x0 + 1, y0) * fx
    bot = v(x0, y0 + 1) * (1 - fx) + v(x0 + 1, y0 + 1) * fx
    return top * (1 - fy) + bot * fy


def wallpaper(x0, y0, w, h):
    out = [f'<rect x="{n(x0)}" y="{n(y0)}" width="{n(w)}" height="{n(h)}" fill="{BG}"/>',
           f'<rect x="{n(x0)}" y="{n(y0)}" width="{n(w)}" height="{n(h)}" fill="url(#glow)"/>']
    cell = 24
    layers = ([], [], [])
    for cy in range(int(y0 // cell) - 1, int((y0 + h) // cell) + 1):
        for cx in range(int(x0 // cell) - 1, int((x0 + w) // cell) + 1):
            rnd = random.Random(cx * 7919 + cy * 104729)
            dens = _density(cx * cell, cy * cell) ** 2.2
            for _ in range(int(dens * 14)):
                bx = cx * cell + rnd.random() * cell
                by = cy * cell + rnd.random() * cell
                s = rnd.choice((2, 2, 3, 3, 4, 5))
                if bx + s < x0 or by + s < y0 or bx > x0 + w or by > y0 + h:
                    continue
                layers[rnd.choices((0, 1, 2), (6, 3, 1))[0]].append(f"M{bx:.0f} {by:.0f}h{s}v{s}h-{s}z")
    for colour, d in zip(("#1c1c1c", "#2a0909", "#3a3a3a"), layers):
        if d:
            out.append(f'<path fill="{colour}" d="{"".join(d)}"/>')
    return "".join(out)


def scanlines(x0, y0, w, h):
    return f'<rect x="{n(x0)}" y="{n(y0)}" width="{n(w)}" height="{n(h)}" fill="url(#scan)" pointer-events="none"/>'


def pill(x, y, w, h, label, fill="#ff4a4a", cls=""):
    return (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="3" fill="#150404" stroke="{EDGE}"/>'
            + text(label, x + w / 2, y + h / 2, fill, "ter-u14n", anchor="middle", mid=True, cls=cls))


def waybar(stats):
    out = [f'<rect width="{W}" height="{BAR - 2}" fill="#0b0b0b"/>',
           f'<rect y="{BAR - 2}" width="{W}" height="2" fill="#9a0000"/>',
           f'<path d="M24 {BAR / 2 - 8}l7 7-7 7-7-7z" fill="{RED}"/>',
           text("SYN-OS", 38, BAR / 2, RED, "ter-u16b", mid=True)]
    wx = 38 + width("SYN-OS", "ter-u16b") + 14
    for i in range(4):
        on = i == 0
        out.append(f'<rect x="{wx + i * 24}" y="{BAR / 2 - 10}" width="18" height="18" rx="2" '
                   f'fill="{RED if on else "#160404"}" stroke="{RED if on else EDGE}"/>')
        out.append(text(str(i + 1), wx + i * 24 + 9, BAR / 2 - 1, "#0b0b0b" if on else DIM, "ter-u12n",
                        anchor="middle", mid=True))
    # An image can't tell the time, so the clock module shows the day it was drawn.
    mods = ["npc.syntax990.com", "ARCH | LFS", stats["today"]]
    x = W - 14
    for label in reversed(mods):
        w = width(label) + 18
        x -= w
        out.append(pill(x, 7, w, 24, label))
        x -= 6
    left = wx + 4 * 24
    out.append(text("everything on this desktop opens", (left + x) / 2, BAR / 2 - 1, "#9a9a9a", "ter-u14n",
                    anchor="middle", mid=True))
    return "".join(out)


def window(x, y, w, h, title, right=""):
    out = [f'<rect x="{x + 6}" y="{y + 6}" width="{w}" height="{h}" fill="#000" fill-opacity=".55"/>',
           f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" fill="{WIN}" stroke="{EDGE}"/>',
           f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="25" fill="#160404"/>',
           f'<rect x="{x + 1}" y="{y + 26}" width="{w - 2}" height="1" fill="#9a0000"/>',
           text(title, x + 12, y + 13.5, TEXT, mid=True)]
    if right:
        out.append(text(right, x + w - 66, y + 13.5, DIM, "ter-u12n", anchor="end", mid=True))
    for i, colour in enumerate(("#3a0b0b", "#3a0b0b", RED)):
        out.append(f'<rect x="{x + w - 52 + i * 16}" y="{y + 8}" width="11" height="11" fill="{colour}"/>')
    return "".join(out)


def svg(box, body, label):
    x0, y0, w, h = box
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{n(x0)} {n(y0)} {n(w)} {n(h)}" '
            f'width="{n(w)}" height="{n(h)}" role="img" aria-label="{esc(label)}">'
            f"<style>{CSS}</style>{DEFS}{body}</svg>\n")


# GitHub.

QUERY = """query($login:String!){user(login:$login){
 company avatarUrl
 contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
 repositories(ownerAffiliations:OWNER,isFork:false,first:100){nodes{isPrivate stargazerCount
  languages(first:20,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""


def fetch(url, data=None, token=None):
    headers = {"User-Agent": f"{LOGIN}-desktop"}
    if token:
        headers["Authorization"] = f"bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), r.headers.get_content_type()


def github():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("build.py: needs GH_TOKEN or GITHUB_TOKEN")
    body, _ = fetch("https://api.github.com/graphql",
                    json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(), token)
    data = json.loads(body)
    if "errors" in data:
        sys.exit(f"build.py: {data['errors']}")
    return data["data"]["user"]


def numbers(user):
    conf = CONF.get("stats", {})
    repos = [r for r in user["repositories"]["nodes"] if conf.get("private") or not r["isPrivate"]]
    skip = set(conf.get("exclude", []))
    langs, colours = {}, {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            if name not in skip:
                langs[name] = langs.get(name, 0) + e["size"]
                colours[name] = e["node"]["color"] or GREY
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:8]

    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"][-52:]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if counts and counts[i] == 0:
        i -= 1                      # today isn't over yet
    current = 0
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    busiest = max(days, key=lambda d: d["contributionCount"])
    return {
        "languages": [(name, size / total, colours[name]) for name, size in top],
        "weeks": [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks],
        "week_starts": [w["contributionDays"][0]["date"] for w in weeks],
        "contributions": cal["totalContributions"],
        "current": current,
        "longest": longest,
        "busiest": busiest,
        "repos": len(repos),
        "stars": sum(r["stargazerCount"] for r in repos),
        "company": (user.get("company") or "").lstrip("@").strip(),
        "avatar": user["avatarUrl"],
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "today": datetime.datetime.now(datetime.timezone.utc).strftime("%a %d %b"),
    }


# The README desktop.

DESKTOP_ICONS = [
    ("folder", "Documents"), ("picture", "Pictures"), ("bin", "Tools"), ("disc", "SYN-OS"),
    ("dish", "Biogenesis"), ("mail", "Mail"), ("play", "YouTube"),
]


def band_a(stats):
    top, h = BAND_A
    bar = waybar(stats)
    tiles = {}
    for i, (kind, label) in enumerate(DESKTOP_ICONS):
        box = (i * ICON_W, top, ICON_W, h)
        cx = i * ICON_W + ICON_W / 2
        delay = f"animation-delay:{.15 + i * .08:.2f}s"
        body = (wallpaper(*box) + bar
                + icon(kind, cx - 24, 54, cls="fi", style=delay)
                + text(label, cx + 1, 111, "#000", anchor="middle", cls="fi", style=delay)
                + text(label, cx, 110, TEXT, anchor="middle", cls="fi", style=delay)
                + scanlines(*box))
        tiles[f"a{i + 1}"] = svg(box, body, f"{label} icon")

    x0 = ICONS_N * ICON_W
    box = (x0, top, W - x0, h)
    note = CONF["notice"]
    tx, ty, tw, th = x0 + 10, 50, W - x0 - 22, 92
    lines = wrap(note["body"], 33, 3)
    toast = [f'<g class="toast">',
             f'<rect x="{tx + 5}" y="{ty + 5}" width="{tw}" height="{th}" fill="#000" fill-opacity=".5"/>',
             f'<rect x="{tx + 1}" y="{ty + 1}" width="{tw - 2}" height="{th - 2}" fill="#120303" stroke="{RED}" stroke-width="2"/>',
             f'<rect class="pulse" x="{tx - 1}" y="{ty - 1}" width="{tw + 2}" height="{th + 2}" fill="none" stroke="#ff7a7a" stroke-width="1"/>',
             f'<path d="M{tx + 22} {ty + 10}l12 12-12 12-12-12z" fill="{RED}"/>',
             f'<path d="M{tx + 22} {ty + 16}l6 6-6 6-6-6z" fill="#120303"/>',
             text(note["title"], tx + 46, ty + 8, "#ffffff", "ter-u16b")]
    for j, line in enumerate(lines):
        toast.append(text(line, tx + 46, ty + 28 + j * 15, "#c8c8c8"))
    toast.append(text("notice · click to open →", tx + tw - 10, ty + th - 16, DIM, "ter-u12n", anchor="end"))
    toast.append("</g>")
    body = wallpaper(*box) + bar + "".join(toast) + scanlines(*box)
    tiles["a8"] = svg(box, body, f"Notice: {note['title']}. {note['body']}")
    return tiles


def avatar(url):
    sep = "&" if "?" in url else "?"
    data, kind = fetch(f"{url}{sep}s=400")
    return f"data:{kind};base64,{base64.b64encode(data).decode()}"


def band_b(stats):
    top, h = BAND_B
    tiles = {}

    # fastfetch, in foot.
    box = (0, top, 600, h)
    x, y, w, wh = 12, top + 12, 576, h - 26
    out = [wallpaper(*box), window(x, y, w, wh, "foot — syn990@npc: ~")]
    py = y + 38
    prompt_w = width("syn990@npc:~$ ", "ter-u16n")
    out.append(text("syn990", x + 16, py, TEAL, "ter-u16n"))
    out.append(text("@npc", x + 16 + 48, py, "#5fb8ad", "ter-u16n"))
    out.append(text(":~$ ", x + 16 + 80, py, GREY, "ter-u16n"))
    cmd = "fastfetch"
    cx = x + 16 + prompt_w
    out.append(text(cmd, cx, py, TEXT, "ter-u16n"))
    typed = width(cmd, "ter-u16n")
    out.append(f'<g style="transform:translateX({n(typed)}px);animation:type .5s steps({len(cmd)}) .35s both">'
               f'<rect x="{n(cx + 8)}" y="{py - 1}" width="{n(typed + 8)}" height="18" fill="{WIN}"/>'
               f'<rect x="{n(cx)}" y="{py}" width="8" height="16" fill="{RED}" style="animation:fi .2s 1s reverse both"/></g>')
    out.append(f"<style>@keyframes type{{from{{transform:translateX(0)}}to{{transform:translateX({n(typed)}px)}}}}</style>")

    ax, ay, asz = x + 16, py + 28, 200
    out.append(f'<g class="glitch"><image x="{ax}" y="{ay}" width="{asz}" height="{asz}" href="{avatar(stats["avatar"])}"/>'
               f'<rect x="{ax}" y="{ay}" width="{asz}" height="{asz}" fill="url(#scan)"/>'
               f'<rect x="{ax - .5}" y="{ay - .5}" width="{asz + 1}" height="{asz + 1}" fill="none" stroke="{RED}"/></g>')

    years = datetime.date.today().year - SINCE
    info = [
        ("OS", "SYN-OS on Arch or LFS 13.1"),
        ("WM", "labwc"),
        ("Bar", "waybar"),
        ("Term", "foot"),
        ("Shell", "zsh"),
        ("Editor", "nano"),
        ("Theme", "SYN-OS-RED, 1 of 63"),
        ("Uptime", f"{years} years, since {SINCE}"),
    ]
    if stats["company"]:
        info.append(("Company", stats["company"]))
    info.append(("Mail", "william@npc.syntax990.com"))
    ix = ax + asz + 20
    iy = ay - 2
    out.append(text("syn990", ix, iy, RED, "ter-u16b", cls="fi", style="animation-delay:1.2s"))
    out.append(text("@npc", ix + 48, iy, TEXT, "ter-u16b", cls="fi", style="animation-delay:1.2s"))
    out.append(text("William Hayward-Holland", ix, iy + 18, TEXT, "ter-u16n", cls="fi", style="animation-delay:1.3s"))
    out.append(f'<rect class="fi" style="animation-delay:1.3s" x="{ix}" y="{iy + 38}" width="{width("William Hayward-Holland", "ter-u16n")}" height="1" fill="{DIM}"/>')
    for j, (k, v) in enumerate(info):
        d = f"animation-delay:{1.4 + j * .09:.2f}s"
        ly = iy + 44 + j * 17
        out.append(text(k, ix, ly, "#ff4a4a", "ter-u14b", cls="fi", style=d))
        out.append(text(v, ix + 64, ly, "#d0d0d0", "ter-u14n", cls="fi", style=d))
    swatch_y = iy + 44 + len(info) * 17 + 8
    for j, colour in enumerate(("#070707", "#3a0000", "#7a0000", "#b30000", RED, "#ff7a7a", TEAL, TEXT)):
        out.append(f'<rect class="fi" style="animation-delay:{2.4 + j * .04:.2f}s" x="{ix + j * 30}" y="{swatch_y}" width="26" height="12" fill="{colour}"/>')
    end_y = y + wh - 30
    out.append(f'<g class="fi" style="animation-delay:2.7s">'
               + text("syn990", x + 16, end_y, TEAL, "ter-u16n") + text("@npc", x + 64, end_y, "#5fb8ad", "ter-u16n")
               + text(":~$ ", x + 96, end_y, GREY, "ter-u16n")
               + f'<rect class="blink" x="{n(x + 16 + prompt_w)}" y="{end_y}" width="8" height="16" fill="{RED}"/></g>')
    out.append(scanlines(*box))
    tiles["b1"] = svg(box, "".join(out), "fastfetch in a foot terminal: William Hayward-Holland, SYN-OS")

    # feh, cycling through tools/media.
    box = (600, top, 400, h)
    x, y, w, wh = 612, top + 12, 376, h - 26
    shows = CONF.get("slideshow", [])
    out = [wallpaper(*box), window(x, y, w, wh, "feh — ~/Pictures", f"{len(shows)} files")]
    iw, ih = 344, 258
    ix, iy = x + (w - iw) / 2, y + 36
    out.append(f'<rect x="{ix - 1}" y="{iy - 1}" width="{iw + 2}" height="{ih + 2}" fill="#000" stroke="{EDGE}"/>')
    period = 4 * len(shows)
    for j, s in enumerate(shows):
        data = base64.b64encode((ROOT / "tools/media" / s["file"]).read_bytes()).decode()
        cls = "slide first" if j == 0 else "slide"
        st = f"animation-duration:{period}s;animation-delay:{j * 4}s"
        out.append(f'<g class="{cls}" style="{st}">'
                   f'<image x="{n(ix)}" y="{n(iy)}" width="{iw}" height="{ih}" href="data:image/jpeg;base64,{data}"/>'
                   + text(f"{j + 1}/{len(shows)}  {s['caption']}", x + w / 2, iy + ih + 14, "#b0b0b0", "ter-u12n", anchor="middle")
                   + "</g>")
    out.append(f'<rect x="{n(ix)}" y="{n(iy)}" width="{iw}" height="{ih}" fill="url(#scan)"/>')
    out.append(scanlines(*box))
    if period:
        out.append(f"<style>@keyframes slide{{0%{{opacity:0}}{n(.5 / period * 100)}%,{n(4 / period * 100)}%{{opacity:1}}{n(4.5 / period * 100)}%,100%{{opacity:0}}}}</style>")
    tiles["b2"] = svg(box, "".join(out), "feh slideshow of SYN-OS and SYN-BIOGENESIS screenshots")
    return tiles


def band_c(stats):
    top, h = BAND_C
    box = (0, top, W, h)
    x, y, w, wh = 12, top + 12, W - 24, h - 24
    out = [wallpaper(*box), window(x, y, w, wh, f"syn-sysmon — github.com/{LOGIN}", f"updated {stats['updated']}")]
    body_y = y + 38

    # Languages, like CPU cores.
    lx = x + 16
    out.append(text("LANGUAGES", lx, body_y, RED, "ter-u14b"))
    out.append(text("public work" if not CONF.get("stats", {}).get("private") else "all work", lx + 360, body_y + 2, DIM, "ter-u12n", anchor="end"))
    langs = stats["languages"]
    top_share = langs[0][1] if langs else 1
    for j, (name, share, colour) in enumerate(langs):
        ry = body_y + 26 + j * 26
        d = f"animation-delay:{.4 + j * .07:.2f}s"
        out.append(f'<rect x="{lx}" y="{ry + 1}" width="4" height="12" fill="{colour}"/>')
        out.append(text(name[:12], lx + 10, ry, "#d0d0d0"))
        out.append(f'<rect x="{lx + 112}" y="{ry + 2}" width="200" height="10" fill="#1a0505"/>')
        out.append(f'<rect class="bar" style="{d}" x="{lx + 112}" y="{ry + 2}" width="{n(max(2, 200 * share / top_share))}" height="10" fill="url(#barfill)"/>')
        out.append(text(f"{share * 100:.1f}%", lx + 360, ry, "#b0b0b0", anchor="end"))

    # Contributions, like a CPU history graph.
    gx, gw = x + 400, 400
    out.append(text("CONTRIBUTIONS · 52 WEEKS", gx, body_y, RED, "ter-u14b"))
    weeks = stats["weeks"]
    peak = max(weeks) or 1
    out.append(text(f"peak {peak:,}/week", gx + gw, body_y + 2, DIM, "ter-u12n", anchor="end"))
    chart_top, chart_h = body_y + 26, 160
    for k in range(5):
        gy = chart_top + chart_h * k / 4
        out.append(f'<rect x="{gx}" y="{n(gy)}" width="{gw}" height="1" fill="#1e0707"/>')
    bw = gw / max(len(weeks), 1)
    for j, c in enumerate(weeks):
        bh = chart_h * c / peak
        if c and bh < 2:
            bh = 2
        if bh:
            out.append(f'<rect class="grow" style="animation-delay:{.6 + j * .025:.3f}s" x="{n(gx + j * bw + 1)}" '
                       f'y="{n(chart_top + chart_h - bh)}" width="{n(bw - 2)}" height="{n(bh)}" fill="url(#barfill)"/>')
    last = None
    for j, start in enumerate(stats["week_starts"]):
        month = datetime.date.fromisoformat(start).strftime("%b")
        if month != last and j < len(weeks) - 2:
            out.append(text(month, gx + j * bw, chart_top + chart_h + 6, GREY, "ter-u12n"))
            last = month

    # Counters, like the RAM and disk readouts.
    cx = x + 830
    b = stats["busiest"]
    public = not CONF.get("stats", {}).get("private")
    counters = [
        ("CONTRIBUTIONS", f"{stats['contributions']:,}", "last 12 months"),
        ("CURRENT STREAK", f"{stats['current']} days", ""),
        ("LONGEST STREAK", f"{stats['longest']} days", ""),
        ("BUSIEST DAY", f"{b['contributionCount']}", datetime.date.fromisoformat(b["date"]).strftime("%d %b %Y")),
        ("REPOS · STARS", f"{stats['repos']} · {stats['stars']}", "public" if public else ""),
    ]
    room = x + w - 12 - cx
    for j, (label, value, note) in enumerate(counters):
        d = f"animation-delay:{.9 + j * .12:.2f}s"
        cy = body_y + j * 46
        vw = width(value, "ter-u16b", 1.25)
        out.append(text(label, cx, cy, DIM, "ter-u12n", cls="fi", style=d))
        out.append(text(value, cx, cy + 14, "#ffffff", "ter-u16b", scale=1.25, cls="fi", style=d))
        if note and vw + 8 + width(note, "ter-u12n") <= room:
            out.append(text(note, cx + vw + 8, cy + 22, GREY, "ter-u12n", cls="fi", style=d))
    out.append(scanlines(*box))
    return {"c1": svg(box, "".join(out), f"syn-sysmon: {stats['contributions']:,} contributions in the last year, top languages "
                      + ", ".join(f"{name} {share * 100:.0f}%" for name, share, _ in langs[:4]))}


# Pages: a title bar for each, and the folder views.

def pages():
    """Every page under home/ and usr/, with its slug, app and title."""
    found = []
    for path in sorted(list(ROOT.glob("home/**/*.md")) + list(ROOT.glob("usr/**/*.md"))):
        rel = PurePosixPath(path.relative_to(ROOT).as_posix())
        parts = list(rel.parts)
        if parts[-1] == "README.md":
            parts = parts[:-1]
        else:
            parts[-1] = rel.stem
        slug = "-".join(parts)
        shown = ("~/" + "/".join(rel.parts[1:])) if rel.parts[0] == "home" else "/" + "/".join(rel.parts)
        shown = shown.removesuffix("/README.md")
        if rel.parts[:2] == ("usr", "bin") and rel.name != "README.md":
            app, title = "foot", f"man {rel.stem}"
        elif rel.name == "whoami.md":
            app, title = "foot", "whoami"
        elif "Pictures" in rel.parts:
            app, title = "feh", shown
        else:
            app, title = "syn-shell", shown
        found.append((slug, app, title))
    return found


CHROME_H = 76


def chrome(stats, app, title):
    box = (0, 0, W, CHROME_H)
    y = BAR
    body = [f'<rect width="{W}" height="{CHROME_H}" fill="{BG}"/>', waybar(stats),
            f'<rect y="{y}" width="{W}" height="{CHROME_H - y}" fill="#160404"/>',
            f'<rect y="{CHROME_H - 1}" width="{W}" height="1" fill="#9a0000"/>',
            text(app, 16, y + 18, RED, "ter-u16b", mid=True),
            text("— " + title, 16 + width(app, "ter-u16b") + 8, y + 18, TEXT, "ter-u16n", mid=True),
            text("click the title bar for the desktop", W - 76, y + 18, DIM, "ter-u12n", anchor="end", mid=True)]
    for i, colour in enumerate(("#3a0b0b", "#3a0b0b", RED)):
        body.append(f'<rect x="{W - 62 + i * 18}" y="{y + 11}" width="13" height="13" fill="{colour}"/>')
    body.append(text("×", W - 62 + 36 + 6.5, y + 18, "#160404", "ter-u14b", anchor="middle", mid=True))
    body.append(scanlines(*box))
    return svg(box, "".join(body), f"{app}: {title}. Click to go back to the desktop.")


TOOLS = ["syn-connect", "syn-relay", "syn-sysmon", "syn-audio", "syn-shell",
         "syn-crypter", "syn-wallgen", "syn-uplink-dialpad", "syn-bar-core", "syn-iso-builder"]

FOLDERS = {
    "home-Documents": [
        ("doc", "SYN-OS.md", "the desktop, Arch or LFS"),
        ("doc", "SYN-BIOGENESIS.md", "artificial life in C11"),
        ("doc", "SYN-RTOS.md", "where it started, 2021"),
        ("doc", "boosteroid-arch.md", "cloud gaming on Arch"),
        ("log", "history.md", "since 2017"),
    ],
    "usr-bin": [("exec", t, "man page") for t in TOOLS],
}
ITEM_W, ITEM_H, STATUS_H = 200, 150, 30


def folder(slug, items):
    tiles = {}
    per_row = W // ITEM_W
    rows = math.ceil(len(items) / per_row)
    for r in range(rows):
        y0 = CHROME_H + r * ITEM_H
        h = ITEM_H + (STATUS_H if r == rows - 1 else 0)
        for c in range(per_row):
            k = r * per_row + c
            x0 = c * ITEM_W
            box = (x0, y0, ITEM_W, h)
            out = [f'<rect x="{x0}" y="{y0}" width="{ITEM_W}" height="{h}" fill="{WIN}"/>',
                   f'<rect x="0" y="{CHROME_H}" width="1" height="2000" fill="{EDGE}"/>',
                   f'<rect x="{W - 1}" y="{CHROME_H}" width="1" height="2000" fill="{EDGE}"/>']
            if k < len(items):
                kind, name, meta = items[k]
                mx = x0 + ITEM_W / 2
                d = f"animation-delay:{.1 + k * .05:.2f}s"
                out.append(icon(kind, mx - 24, y0 + 22, cls="fi", style=d))
                out.append(text(name, mx, y0 + 84, TEXT, anchor="middle", cls="fi", style=d))
                out.append(text(meta, mx, y0 + 104, GREY, "ter-u12n", anchor="middle", cls="fi", style=d))
            if r == rows - 1:
                sy = y0 + ITEM_H
                out.append(f'<rect x="{x0}" y="{sy}" width="{ITEM_W}" height="{STATUS_H}" fill="#160404"/>')
                out.append(f'<rect x="{x0}" y="{sy}" width="{ITEM_W}" height="1" fill="{EDGE}"/>')
                out.append(f'<rect x="{x0}" y="{sy + STATUS_H - 1}" width="{ITEM_W}" height="1" fill="#9a0000"/>')
                out.append(text(f"{len(items)} items", 16, sy + STATUS_H / 2, GREY, "ter-u12n", mid=True))
                out.append(text("click a file to open it", W - 16, sy + STATUS_H / 2, DIM, "ter-u12n", anchor="end", mid=True))
            out.append(scanlines(*box))
            label = f"{items[k][1]}: {items[k][2]}" if k < len(items) else "empty"
            tiles[f"{slug}-{r}{c}"] = svg(box, "".join(out), label)
    return tiles


def notice_link(sync):
    """The README's link around the notice has to follow desktop.toml."""
    readme = ROOT / "README.md"
    page = readme.read_text(encoding="utf-8")
    tile = page.index("desktop/a8.svg")
    start = page.rindex('<a href="', 0, tile) + len('<a href="')
    end = page.index('"', start)
    want = CONF["notice"]["link"]
    if page[start:end] == want:
        return
    if not sync:
        sys.exit(f"build.py: README.md links the notice to {page[start:end]}, desktop.toml to {want}; "
                 "run python3 tools/build.py --sync and commit README.md")
    readme.write_text(page[:start] + want + page[end:], encoding="utf-8")
    print(f"README.md: notice now links to {want}", file=sys.stderr)


def main():
    if sys.argv[1:] == ["--sync"]:
        notice_link(sync=True)
        return
    if len(sys.argv) > 1:
        sys.exit(__doc__)
    notice_link(sync=False)
    out = ROOT / "var"
    stats = numbers(github())
    written = {}
    for name, body in {**band_a(stats), **band_b(stats), **band_c(stats)}.items():
        written[f"desktop/{name}.svg"] = body
    for slug, app, title in pages():
        written[f"chrome/{slug}.svg"] = chrome(stats, app, title)
    for slug, items in FOLDERS.items():
        for name, body in folder(slug, items).items():
            written[f"folders/{name}.svg"] = body
    for sub in ("desktop", "chrome", "folders"):
        shutil.rmtree(out / sub, ignore_errors=True)
    for rel, body in written.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print(f"{len(written)} tiles, {sum(len(b) for b in written.values()) // 1024} KB, "
          f"{stats['contributions']:,} contributions, {stats['repos']} repos", file=sys.stderr)


if __name__ == "__main__":
    main()
