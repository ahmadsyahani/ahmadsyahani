import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import textwrap
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
USER = 'ahmadsyahani'
CARDS = ROOT / 'cards'
ASSETS = ROOT / 'assets'
DATA = ROOT / 'data'
for folder in (CARDS, ASSETS, DATA):
    folder.mkdir(exist_ok=True)


def fetch(url):
    request = Request(url, headers={'User-Agent': 'ahmadsyahani-profile'})
    with urlopen(request, timeout=30) as response:
        return response.read()


if '--refresh' in __import__('sys').argv:
    profile = json.loads(fetch(f'https://api.github.com/users/{USER}'))
    (DATA / 'profile.json').write_text(json.dumps(profile), encoding='utf-8')
    (DATA / 'repos.json').write_bytes(fetch(f'https://api.github.com/users/{USER}/repos?sort=pushed&per_page=100'))
    (DATA / 'contributions.html').write_bytes(fetch(f'https://github.com/users/{USER}/contributions'))
    (ASSETS / 'avatar.png').write_bytes(fetch(profile['avatar_url']))

profile = json.loads((DATA / 'profile.json').read_text(encoding='utf-8-sig'))
repos = json.loads((DATA / 'repos.json').read_text(encoding='utf-8-sig'))
calendar = (DATA / 'contributions.html').read_text(encoding='utf-8-sig')
PAPER, INK, BLUE = '#f3f3f1', '#171717', '#2f55ff'


def text(x, y, value, size=16, color=INK, family='Arial, sans-serif', extra=''):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}" {extra}>{html.escape(str(value))}</text>'


def card(name, height, body, width=880, background=PAPER):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
           f'<title>{html.escape(name.replace("-", " "))} | Ahmad Syahani</title>'
           '<style>@keyframes enter{from{opacity:0}to{opacity:1}}.enter{animation:enter 1.2s ease-out both}'
           '@media(prefers-reduced-motion:reduce){.enter{animation:none!important}}</style>'
           f'<rect width="{width}" height="{height-12}" rx="14" fill="{background}"/>{body}</svg>')
    ET.fromstring(svg)
    (CARDS / f'{name}.svg').write_text(svg, encoding='utf-8')


# Crop the monitor out while keeping the ears, eyes, and chest of the avatar cat.
image = Image.open(ASSETS / 'avatar.png').convert('L')
w, h = image.size
image = ImageOps.autocontrast(image.crop((int(w*.10), int(h*.24), int(w*.91), int(h*.98))))
cols, rows = 100, 53
image = image.resize((cols, rows), Image.Resampling.LANCZOS)
ramp = '@%#*+=-:. '
lines = [''.join(ramp[min(9, p*10//256)] for p in list(image.getdata())[r*cols:(r+1)*cols]) for r in range(rows)]
(ASSETS / 'portrait.txt').write_text('\n'.join(lines), encoding='utf-8')
portrait = ''.join(text(0, 6+r*6.5, line, 6.5, INK, 'monospace', 'xml:space="preserve" textLength="320" lengthAdjust="spacing"') for r, line in enumerate(lines))
card('portrait', 380, f'<g transform="translate(20 10)">{portrait}</g>', 360)
hero = text(44, 58, 'AHMADSYAHANI / GITHUB', 12, BLUE)
hero += text(42, 128, 'Ahmad', 66, family='Georgia, serif') + text(42, 198, 'Syahani.', 66, family='Georgia, serif')
hero += text(44, 242, 'Frontend & full-stack development', 19)
hero += text(44, 274, profile['location'], 15, '#555555')
hero += text(44, 314, 'PHP / TypeScript / Dart', 14, BLUE)
hero += text(44, 349, 'ahmadsyahani.app', 15)
hero += f'<g class="enter" transform="translate(510 24)">{portrait}</g>'
card('hero', 410, hero)

tooltips = {}
for attrs, content in re.findall(r'<tool-tip\b([^>]*)>(.*?)</tool-tip>', calendar, re.S):
    match = re.search(r'for="([^"]+)"', attrs)
    if match:
        tooltips[match[1]] = html.unescape(re.sub('<[^>]+>', '', content)).strip()
days = []
for attrs in re.findall(r'<td\b([^>]*)>', calendar):
    values = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
    if not values.get('data-date') or 'data-level' not in values:
        continue
    tooltip = tooltips.get(values.get('id'))
    if not tooltip:
        raise ValueError('Missing contribution tooltip; refusing to publish guessed counts')
    count = re.match(r'([\d,]+) contribution', tooltip)
    if count:
        count = int(count[1].replace(',', ''))
    elif tooltip.lower().startswith('no contributions'):
        count = 0
    else:
        raise ValueError(f'Unknown contribution format: {tooltip}')
    days.append((values['data-date'], count, int(values['data-level'])))
days.sort()
assert len(days) >= 350 and len({d[0] for d in days}) == len(days), 'Incomplete calendar'
total = sum(d[1] for d in days)
active = sum(d[1] > 0 for d in days)
lead = (dt.date.fromisoformat(days[0][0]).weekday()+1)%7
graph = text(40, 52, 'A year of building.', 32, family='Georgia, serif')
graph += text(40, 80, f'{days[0][0]} to {days[-1][0]} / GitHub contributions', 12, '#555555')
colors = ['#deded9', '#c6d0ff', '#91a5ff', '#5b78ff', BLUE]
for i, (date, count, level) in enumerate(days):
    col, row = divmod(i+lead, 7)
    graph += f'<rect x="{40+col*15}" y="{103+row*15}" width="12" height="12" rx="2" fill="{colors[level]}"><title>{date}: {count} contributions</title></rect>'
graph += text(40, 242, f'{total:,} contributions   /   {active} active days', 15)
graph += text(40, 268, f'Updated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d} UTC', 11, '#555555')
card('heatmap', 300, graph)

tiles = [('build', 'BUILD', 'Web', 'PHP / TypeScript', BLUE, '#ffffff'),
         ('mobile', 'MOBILE', 'Apps', 'Dart projects', '#df392b', '#ffffff'),
         ('code', 'CODE', str(profile['public_repos']), 'Public repositories', '#ffc81a', INK)]
for name, label, main, subtitle, color, foreground in tiles:
    body = text(25, 40, label, 12, foreground)
    body += text(23, 106, main, 51, foreground, 'Georgia, serif')
    body += text(25, 150, subtitle, 15, foreground)
    card(name, 192, body, 293, color)

by_name = {r['name']: r for r in repos}
selected = ['ShipX-Delivery', 'Nexa', 'ahmadsyahani.app']
for name in selected:
    repo = by_name[name]
    body = text(22, 38, repo['language'] or 'Repository', 12, BLUE)
    body += text(22, 79, name, 22, family='Georgia, serif')
    description = repo.get('description') or f"{repo['language'] or 'Code'} project by @{USER}."
    for i, line in enumerate(textwrap.wrap(description, 29)[:3]):
        body += text(22, 112+i*21, line, 14, '#555555')
    body += text(22, 207, f"{repo['stargazers_count']} stars / {repo['forks_count']} forks", 12, '#555555')
    card(f'repo-{name}', 244, body, 293)

readme = '<div align="center">\n'
readme += '<a href="https://ahmadsyahani.app"><img src="./cards/hero.svg" width="100%" alt="Ahmad Syahani, frontend and full-stack development, Surabaya. ASCII art from my GitHub cat avatar." /></a><br>\n'
readme += '<img src="./cards/heatmap.svg" width="100%" alt="GitHub contributions for the past year, refreshed daily" /><br>\n'
for name, target, alt in [('build','https://github.com/ahmadsyahani?tab=repositories','Web development: PHP and TypeScript'),('mobile','https://github.com/ahmadsyahani/Nexa','Mobile apps: Dart'),('code','https://github.com/ahmadsyahani?tab=repositories','Public GitHub repositories')]:
    readme += f'<a href="{target}"><img src="./cards/{name}.svg" width="33%" alt="{alt}" /></a>'
readme += '\n</div>\n\n## What I’m coding\n\n<div align="center">\n'
for name in selected:
    readme += f'<a href="https://github.com/{USER}/{name}"><img src="./cards/repo-{name}.svg" width="33%" alt="{name} repository" /></a>'
readme += '\n</div>\n\n<p align="center"><a href="https://ahmadsyahani.app">Website</a> &nbsp;/&nbsp; <a href="https://github.com/ahmadsyahani">GitHub</a></p>\n'
(ROOT / 'README.md').write_text(readme, encoding='utf-8')
assert len(lines) == 53 and all(len(line) == 100 for line in lines)
for path in re.findall(r'src="\./([^"]+)"', readme):
    assert (ROOT / path).is_file(), path
print(f'Rendered {len(list(CARDS.glob("*.svg")))} SVG cards; {len(days)} days; {total} contributions')
