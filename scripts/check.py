#!/usr/bin/env python3
"""Dependency-free integrity check of CMET's GitHub Pages distribution."""
from pathlib import Path
from html.parser import HTMLParser
from hashlib import sha256
from collections import defaultdict
import json, sys

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []

class Resources(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag in ('img','script','link','source','a'):
            for key in ('src','href','srcset'):
                if a.get(key):
                    value = a[key]
                    if key == 'srcset':
                        value = value.split(',')[0].strip().split(' ')[0]
                    self.links.append((tag, value))
        for k in ('data-large',):
            if a.get(k): self.links.append((tag,a[k]))

htmls=sorted(ROOT.rglob('*.html'))
for path in htmls:
    if path.parent == ROOT and path.name not in ('index.html','404.html'):
        ERRORS.append('HTML outside html/ directory: '+path.name)
if len(htmls)<15: ERRORS.append('Missing generated HTML pages')
all_local_references=set()
for path in htmls:
    parser=Resources()
    try: parser.feed(path.read_text(encoding='utf-8'))
    except Exception as e: ERRORS.append(f'{path}: invalid encoding: {e}');continue
    for tag,url in parser.links:
        if url.startswith(('https:','http:','tel:','mailto:','data:','javascript:','#')): continue
        target=url.split('#',1)[0].split('?',1)[0].strip()
        if not target: continue
        ref=(path.parent/target).resolve()
        if not ref.is_relative_to(ROOT) or not ref.is_file():
            ERRORS.append(f'{path.relative_to(ROOT)}: link broken -> {url}')
        else: all_local_references.add(ref)

# Relative references inside stylesheets and JS/CSS imports must resolve.
import re
for sheet in ROOT.rglob('*.css'):
    content=sheet.read_text(encoding='utf-8')
    for value in re.findall(r'url\(\s*["\']?([^"\')]+)', content):
        value=value.strip()
        if value.startswith(('data:','http:','https:','//','#')): continue
        dest=(sheet.parent/value.split('?',1)[0].split('#',1)[0]).resolve()
        if not dest.is_relative_to(ROOT) or not dest.is_file():
            ERRORS.append(f'{sheet.relative_to(ROOT)}: missing url() asset: {value}')

required=['index.html','404.html','html/gioi-thieu.html','html/tin-tuc.html',
          'css/site.css','js/site.js','js/config.js',
          'css/vendor/bootstrap.min.css','js/vendor/jquery.min.js',
          'data/content.json','data/asset-sources.json','scripts/build.py']
for f in required:
    if not (ROOT/f).is_file(): ERRORS.append('Missing core file: '+f)

image_dir=ROOT/'images'
images=sorted(f for f in image_dir.rglob('*') if f.is_file())
if not images: ERRORS.append('No images found')
for f in images:
    if f not in all_local_references:
        ERRORS.append('Unused image: '+str(f.relative_to(ROOT)))

catalog=json.loads((ROOT/'data/asset-sources.json').read_text(encoding='utf-8'))
recorded=[ROOT/entry['asset'] for entry in catalog]
for f in recorded:
    if not f.is_file(): ERRORS.append('Catalog entry missing: '+str(f.relative_to(ROOT)))
if set(recorded)!=set(images):
    for f in set(images)-set(recorded): ERRORS.append('Image without source record: '+str(f.relative_to(ROOT)))
if len(recorded)!=len(set(recorded)): ERRORS.append('Duplicated catalog records')

hashes=defaultdict(list)
for f in images: hashes[sha256(f.read_bytes()).hexdigest()].append(f.relative_to(ROOT))
for group in hashes.values():
    if len(group)>1: ERRORS.append('Identical image copies: '+str(group))

for path in ROOT.rglob('*'):
    if any(part in {'__pycache__','.DS_Store','node_modules','Thumbs.db'} for part in path.parts) or path.suffix in {'.pyc','.download','.tmp','.bak','.rar'}:
        ERRORS.append('Temporary/irrelevant file: '+str(path.relative_to(ROOT)))

for gif in ('scholarship-ribbon.gif','official-banner.gif'):
    path=image_dir/'banners'/gif
    if not path.is_file() or path.read_bytes()[:6] not in (b'GIF87a',b'GIF89a'):
        ERRORS.append('Invalid animated banner: '+gif)

print(f'Checked {len(htmls)} HTML pages, {len(images)} images and {len(catalog)} source records.')
if ERRORS:
    for e in ERRORS: print('ERROR:',e)
    sys.exit(1)
print('OK — all local links and source assets resolve, no unused/identical images or junk files.')
