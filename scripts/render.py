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


def card(name, height, body, width=880, background=PAPER, left=0, right=0):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
           f'<title>{html.escape(name.replace("-", " "))} | Ahmad Syahani</title>'
           '<style>@keyframes enter{from{opacity:.7}to{opacity:1}}.enter{animation:enter 1.2s ease-out both}'
           '@media(prefers-reduced-motion:reduce){.enter{animation:none!important}}</style>'
           f'<g transform="translate({left} 0)"><rect width="{width-left-right}" height="{height-20}" rx="14" fill="{background}"/>{body}</g></svg>')
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
    pad = 28 if mobile else 44
    if mobile:
        hero = text(pad, 89, 'Ahmad', 43, weight=600)
        hero += text(pad, 141, 'Syahani.', 43, weight=600)
        hero += f'<g class="enter" transform="translate(236 38) scale(.52)">{portrait}</g>'
        hero += text(pad, 243, 'Frontend & full-stack development', 19)
        hero += text(pad, 279, profile['location'], 15, MUTED)
        hero += text(pad, 313, 'PHP / TypeScript / Dart', 15, BLUE)
    else:
        hero = text(pad, 115, 'Ahmad Syahani.', 55, weight=600)
        hero += text(pad, 161, 'Frontend & full-stack development', 23)
        hero += text(pad, 213, profile['location'], 17, MUTED)
        hero += text(pad, 251, 'PHP / TypeScript / Dart', 17, BLUE)
        hero += text(pad, 289, 'ahmadsyahani.app', 16, MUTED)
        hero += f'<g class="enter" transform="translate(568 30) scale(.79)">{portrait}</g>'
    card('hero'+suffix, 370 if mobile else 360, hero, width)

    graph = text(pad, 58, 'Little by little.', 29 if mobile else 32, weight=600)
    graph += text(pad, 88, f'{total:,} contributions this year', 16, MUTED)
    step = (width-pad*2)/54
    cell = step*.76
    top = 117
    for i, (date, count, level) in enumerate(days):
        col, row = divmod(i+lead, 7)
        graph += f'<rect x="{pad+col*step:.2f}" y="{top+row*step:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="{cell*.2:.2f}" fill="{colors[level]}"><title>{date}: {count} contributions</title></rect>'
    baseline = top+7*step+28
    graph += text(pad, baseline, f'{days[0][0]} to {days[-1][0]}', 12, MUTED)
    card('heatmap'+suffix, int(baseline+58), graph, width)

    monthly = {}
    for date, count, _ in days:
        monthly[date[:7]] = monthly.get(date[:7], 0)+count
    months = list(sorted(monthly.items()))[-12:]
    best = max(day[1] for day in days)
    activity = text(pad, 52, 'The daily rhythm.', 25 if mobile else 28, weight=600)
    activity += text(pad, 88, f'{active} active days', 17, BLUE, weight=600)
    activity += text(pad, 118, f'Busiest day: {best} contributions', 15, MUTED)
    chart_x, chart_y = (pad, 165) if mobile else (410, 38)
    chart_w, chart_h = (width-pad*2, 66) if mobile else (width-454, 83)
    bar_step = chart_w/12
    maximum = max(1, max(count for _,count in months))
    for i,(month,count) in enumerate(months):
        bar_h = max(3, count/maximum*chart_h)
        activity += f'<rect x="{chart_x+i*bar_step:.2f}" y="{chart_y+chart_h-bar_h:.2f}" width="{bar_step-8:.2f}" height="{bar_h:.2f}" rx="3" fill="{BLUE if count else colors[0]}"><title>{month}: {count} contributions</title></rect>'
        activity += text(chart_x+i*bar_step, chart_y+chart_h+22, dt.date.fromisoformat(month+'-01').strftime('%b')[0:1] if mobile else dt.date.fromisoformat(month+'-01').strftime('%b'), 10, MUTED)
    card('activity'+suffix, 303 if mobile else 188, activity, width)

    column = width/3
    for i,(name,label,headline,description,color,foreground) in enumerate([
        ('build','BUILD','Web','PHP / TypeScript',BLUE,'#ffffff'),
        ('mobile','MOBILE','Apps','Dart projects','#e7ecdf',INK),
        ('code','EXPLORE',str(profile['public_repos']),'Public repositories',PAPER,INK),
    ]):
        inset = 12 if mobile else 25
        left, right = [(0,10),(5,5),(10,0)][i]
        body = text(inset, 34 if mobile else 40, label, 11 if mobile else 12, foreground, weight=600)
        body += text(inset, 83 if mobile else 107, headline, 30 if mobile else 48, foreground, weight=600)
        labels = textwrap.wrap(description, 13) if mobile else [description]
        for line_index,line in enumerate(labels):
            body += text(inset, (117 if mobile else 146)+line_index*19, line, 12 if mobile else 16, foreground)
        card(name+suffix, 190 if mobile else 214, body, column, color, left, right)

    heading = text(0, 43, 'On my workbench.', 29 if mobile else 34, weight=600)
    card('projects-title'+suffix, 83, heading, width, 'none')
    for i,name in enumerate(selected):
        repo = by_name[name]
        inset = 12 if mobile else 25
        left, right = [(0,10),(5,5),(10,0)][i]
        body = text(inset, 35 if mobile else 41, repo['language'] or 'Repository', 14 if mobile else 13, BLUE)
        title_lines = [{'ShipX-Delivery':'ShipX', 'Nexa':'Nexa', 'ahmadsyahani.app':'Website'}[name]] if mobile else [name]
        for j,line in enumerate(title_lines):
            body += text(inset, (78 if mobile else 89)+j*24, line, 20 if mobile else 23, weight=600)
        description = repo.get('description') or f"{repo['language'] or 'Code'} project by @{USER}."
        wrapped = {'ShipX-Delivery':['POS &', 'delivery'], 'Nexa':['Dart', 'project'], 'ahmadsyahani.app':['Personal', 'website']}[name] if mobile else textwrap.wrap(description, 27)
        desc_top = 119 if mobile else 128
        for j, line in enumerate(wrapped):
            body += text(inset, desc_top+j*23, line, 16 if mobile else 15, MUTED)
        if not mobile:
            body += text(inset, 240, f"{repo['stargazers_count']} stars", 13, MUTED)
        card('repo-'+name+suffix, 204 if mobile else 288, body, column, PAPER, left, right)


def picture(name, alt, link=None, width='100%', newline=True):
    value = f'<picture><source media="(max-width: 600px)" srcset="./cards/{name}-mobile.svg" /><img src="./cards/{name}.svg" width="{width}" alt="{html.escape(alt, quote=True)}" /></picture>'
    if link:
        value = f'<a href="{link}">{value}</a>'
    return value+('<br>\n' if newline else '')


readme = '<div align="center">\n'
readme += picture('hero', 'Ahmad Syahani. Frontend and full-stack development in Surabaya. ASCII cat from my GitHub avatar.', 'https://ahmadsyahani.app')
readme += picture('heatmap', f'Little by little. {total} GitHub contributions and {active} active days.', f'https://github.com/{USER}?tab=overview')
readme += picture('activity', f'Monthly contributions. {active} active days. Busiest day: {best} contributions.')
for name,alt,link in [('build','Web development: PHP and TypeScript',f'https://github.com/{USER}?tab=repositories'),('mobile','Mobile development: Dart',f'https://github.com/{USER}/Nexa'),('code',f'{profile["public_repos"]} public repositories',f'https://github.com/{USER}?tab=repositories')]:
    readme += picture(name, alt, link, '33.333%', False)
readme += '<br>\n'
readme += picture('projects-title', 'On my workbench. Selected repositories.')
for name in selected:
    readme += picture('repo-'+name, name+' repository', f'https://github.com/{USER}/{name}', '33.333%', False)
readme += '\n'
readme += '\n</div>\n\n<p align="center"><a href="https://ahmadsyahani.app">Website</a> &nbsp;/&nbsp; <a href="https://github.com/ahmadsyahani">GitHub</a></p>\n'
(ROOT / 'README.md').write_text(readme, encoding='utf-8')
assert len(lines) == 53 and all(len(line) == 100 for line in lines)
for path in re.findall(r'src="\./([^"]+)"', readme):
    assert (ROOT / path).is_file(), path
print(f'Rendered {len(list(CARDS.glob("*.svg")))} SVG cards; {len(days)} days; {total} contributions')
