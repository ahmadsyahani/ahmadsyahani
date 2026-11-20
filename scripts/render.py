import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import textwrap
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from functools import lru_cache
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

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
PAPER, INK, BLUE = '#f6f5ef', '#23392e', '#436550'
MUTED = '#58665b'
FONT = ROOT / 'fonts' / 'GoogleSansFlex.ttf'


@lru_cache(maxsize=8)
def font_instance(weight):
    font = TTFont(FONT)
    return instantiateVariableFont(font, {'wght': weight, 'wdth': 100, 'opsz': 24, 'slnt': 0, 'ROND': 25})


@lru_cache(maxsize=4096)
def glyph_path(weight, character):
    font = font_instance(weight)
    name = font.getBestCmap().get(ord(character), '.notdef')
    glyphs = font.getGlyphSet()
    pen = SVGPathPen(glyphs)
    glyphs[name].draw(pen)
    return pen.getCommands(), font['hmtx'][name][0]


def text(x, y, value, size=16, color=INK, family=None, extra='', weight=400):
    if family == 'monospace':
        return f'<text x="{x}" y="{y}" font-family="Consolas, monospace" font-size="{size}" fill="{color}" {extra}>{html.escape(str(value))}</text>'
    scale = size / font_instance(weight)['head'].unitsPerEm
    cursor, parts = 0, []
    for character in str(value):
        path, advance = glyph_path(weight, character)
        if path:
            parts.append(f'<path transform="translate({cursor} 0)" d="{path}"/>')
        cursor += advance
    return f'<g aria-label="{html.escape(str(value), quote=True)}" fill="{color}" transform="translate({x} {y}) scale({scale} {-scale})">{"".join(parts)}</g>'


def card(name, height, body, width=880, background=PAPER):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
           f'<title>{html.escape(name.replace("-", " "))} | Ahmad Syahani</title>'
           '<style>@keyframes enter{from{opacity:0}to{opacity:1}}.enter{animation:enter 1.2s ease-out both}'
           '@media(prefers-reduced-motion:reduce){.enter{animation:none!important}}</style>'
           f'<rect width="{width}" height="{height-28}" rx="16" fill="{background}"/>{body}</svg>')
    ET.fromstring(svg)
    (CARDS / f'{name}.svg').write_text(svg, encoding='utf-8')


# Crop the monitor out while keeping the ears, eyes, and chest of the avatar cat.
image = Image.open(ASSETS / 'avatar.png').convert('L')
w, h = image.size
image = ImageOps.autocontrast(image.crop((int(w*.10), int(h*.24), int(w*.91), int(h*.98))))
cols, rows = 100, 53
image = image.resize((cols, rows), Image.Resampling.LANCZOS)
ramp = '@%#*+=-:. '
pixels = list(image.get_flattened_data()) if hasattr(image, 'get_flattened_data') else list(image.getdata())
lines = [''.join(ramp[min(9, p*10//256)] for p in pixels[r*cols:(r+1)*cols]) for r in range(rows)]
(ASSETS / 'portrait.txt').write_text('\n'.join(lines), encoding='utf-8')
portrait = ''.join(text(0, 6+r*6.5, line, 6.5, INK, 'monospace', 'xml:space="preserve" textLength="320" lengthAdjust="spacing"') for r, line in enumerate(lines))
card('portrait', 380, f'<g transform="translate(20 10)">{portrait}</g>', 360)

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
by_name = {r['name']: r for r in repos}
selected = ['ShipX-Delivery', 'Nexa', 'ahmadsyahani.app']
colors = ['#dce2d6', '#bdcfb4', '#8eac87', '#64815e', '#3f614b']
for width, suffix in [(880, ''), (440, '-mobile')]:
    mobile = bool(suffix)
    pad = 32 if mobile else 56
    hero = text(pad, 91, 'Ahmad', 58 if mobile else 68, weight=600)
    hero += text(pad, 161 if mobile else 173, 'Syahani.', 58 if mobile else 68, weight=600)
    hero += text(pad, 208 if mobile else 225, 'Frontend & full-stack', 22 if mobile else 23)
    hero += text(pad, 239 if mobile else 257, 'development.', 22 if mobile else 23)
    hero += text(pad, 288 if mobile else 310, profile['location'], 16, MUTED)
    hero += text(pad, 322 if mobile else 348, 'ahmadsyahani.app', 17, BLUE)
    if mobile:
        hero += f'<g class="enter" transform="translate(60 365) scale(1)">{portrait}</g>'
    else:
        hero += f'<g class="enter" transform="translate(514 58) scale(.94)">{portrait}</g>'
    card('hero'+suffix, 780 if mobile else 460, hero, width)

    graph = text(pad, 65, 'Little by little.', 32 if mobile else 38, weight=600)
    graph += text(pad, 103, 'My year on GitHub.', 18, MUTED)
    step = (width-pad*2)/54
    cell = step*.76
    top = 137
    for i, (date, count, level) in enumerate(days):
        col, row = divmod(i+lead, 7)
        graph += f'<rect x="{pad+col*step:.2f}" y="{top+row*step:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="{cell*.2:.2f}" fill="{colors[level]}"><title>{date}: {count} contributions</title></rect>'
    baseline = top+7*step+40
    graph += text(pad, baseline, f'{total:,} contributions', 19, weight=600)
    graph += text(pad if mobile else 390, baseline+32 if mobile else baseline, f'{active} active days', 18, MUTED)
    graph += text(pad, baseline+72 if mobile else baseline+38, f'{days[0][0]} to {days[-1][0]}', 13, MUTED)
    card('heatmap'+suffix, int(baseline+136 if mobile else baseline+104), graph, width)

    body = text(pad, 66, 'Web. Mobile. A curious cat.', 25 if mobile else 34, weight=600)
    body += text(pad, 110, 'PHP / TypeScript / Dart', 19, BLUE)
    body += text(pad, 150, f"{profile['public_repos']} public repositories", 17, MUTED)
    card('toolkit'+suffix, 228, body, width, '#e7ecdf')

    heading = text(pad, 65, 'On my workbench.', 32 if mobile else 38, weight=600)
    heading += text(pad, 103, 'A few repositories to look around.', 17, MUTED)
    card('projects-title'+suffix, 157, heading, width)
    for name in selected:
        repo = by_name[name]
        body = text(pad, 67, name, 29 if mobile else 34, weight=600)
        description = repo.get('description') or f"{repo['language'] or 'Code'} project by @{USER}."
        wrapped = textwrap.wrap(description, 34 if mobile else 70)
        for i, line in enumerate(wrapped):
            body += text(pad, 111+i*28, line, 17 if mobile else 19, MUTED)
        meta = 111+len(wrapped)*28+23
        body += text(pad, meta, repo['language'] or 'Repository', 16, BLUE, weight=600)
        body += text(pad, meta+36, f"{repo['stargazers_count']} stars / {repo['forks_count']} forks", 14, MUTED)
        card('repo-'+name+suffix, meta+112, body, width)


def picture(name, alt, link=None):
    value = f'<picture><source media="(max-width: 600px)" srcset="./cards/{name}-mobile.svg" /><img src="./cards/{name}.svg" width="100%" alt="{html.escape(alt, quote=True)}" /></picture>'
    if link:
        value = f'<a href="{link}">{value}</a>'
    return value+'<br>\n'


readme = '<div align="center">\n'
readme += picture('hero', 'Ahmad Syahani. Frontend and full-stack development in Surabaya. ASCII cat from my GitHub avatar.', 'https://ahmadsyahani.app')
readme += picture('heatmap', f'Little by little. {total} GitHub contributions and {active} active days.', f'https://github.com/{USER}?tab=overview')
readme += picture('toolkit', f'PHP, TypeScript, Dart. {profile["public_repos"]} public repositories.', f'https://github.com/{USER}?tab=repositories')
readme += picture('projects-title', 'On my workbench. Selected repositories.')
for name in selected:
    readme += picture('repo-'+name, name+' repository', f'https://github.com/{USER}/{name}')
readme += '\n</div>\n\n<p align="center"><a href="https://ahmadsyahani.app">Website</a> &nbsp;/&nbsp; <a href="https://github.com/ahmadsyahani">GitHub</a></p>\n'
(ROOT / 'README.md').write_text(readme, encoding='utf-8')
assert len(lines) == 53 and all(len(line) == 100 for line in lines)
for path in re.findall(r'src="\./([^"]+)"', readme):
    assert (ROOT / path).is_file(), path
print(f'Rendered {len(list(CARDS.glob("*.svg")))} SVG cards; {len(days)} days; {total} contributions')
