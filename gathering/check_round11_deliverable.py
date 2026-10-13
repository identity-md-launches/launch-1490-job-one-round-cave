#!/usr/bin/env python3
"""Check this round's output contract, source scope, gallery and provenance."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import struct
import subprocess
import sys

from make_thumbnail import png_rgb

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.wall = None
        self.cards = {}
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'section':
            self.wall = a.get('id')
            self.cards[self.wall] = []
        if tag == 'article':
            self.cards[self.wall].append(int(a['data-number']))
        if tag == 'script':
            self.scripts.append(a)


def main():
    baseline = json.loads((ROOT / 'gathering/checks/round-11/line-baseline.json').read_text())
    now = {str(p.relative_to(ROOT)): sha(p) for n in range(1, 5)
           for p in sorted((ROOT / f'line-{n}').rglob('*')) if p.is_file()}
    assert now == baseline, 'line files changed'
    record = json.loads((ROOT / 'dist/gathering/11.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    traits = record['attributes']
    assert [v['trait_type'] for v in traits] == [
        'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing']
    assert all(set(v) == {'trait_type', 'value'} for v in traits)
    assert [traits[i]['value'] for i in (0,1,2,5)] == ['Base','Gathering',11,'Gathering']
    assert type(traits[2]['value']) is int
    wall = ROOT / 'artifacts/gathering/wall-v12.png'
    assert record['image'] == 'https://api.imd.fun/artifacts/' + sha(wall)
    assert wall.read_bytes() == (ROOT / 'artifacts/gathering/wall.png').read_bytes()
    w, h, rows = png_rgb(wall.read_bytes())
    assert (w,h) == (1254,1254)
    jpeg = (ROOT / 'dist/gathering/11.jpg').read_bytes()
    assert jpeg[:2] == b'\xff\xd8' and jpeg[-2:] == b'\xff\xd9'
    pos = jpeg.index(b'\xff\xc0')
    depth, jh, jw = struct.unpack('>BHH',jpeg[pos+4:pos+9])
    assert (depth,jw,jh) == (8,512,512)
    assert len(jpeg) < 100000
    goals = json.loads((ROOT / 'dist/goals.json').read_text())
    assert goals == [{'line':n,'goal':(ROOT / f'line-{n}/GOAL.md').read_text().strip()}
                     for n in range(1,5)]
    gallery = Gallery()
    page = (ROOT / 'dist/index.html').read_text()
    gallery.feed(page)
    assert not gallery.scripts
    total = 0
    for folder in ['line-1','line-2','line-3','line-4','gathering']:
        files = sorted((ROOT / 'dist' / folder).glob('[0-9][0-9].json'), reverse=True)
        painted, pending = [], []
        for file in files:
            item = json.loads(file.read_text())
            if item['name'] == 'Not painted yet':
                assert item == {'name':'Not painted yet',
                    'image':'https://api.imd.fun/artifacts/9cbb7bb2a41efa92e010921f287819c9ffb02c4375fa9496c8468701d8e00cc5',
                    'attributes':[{'trait_type':'Cave','value':'Base'}]}
                assert not file.with_suffix('.jpg').exists()
                pending.append(int(file.stem))
            else:
                painted.append(int(file.stem))
        assert gallery.cards[folder] == painted + pending
        assert all((ROOT/'dist'/folder/f'{n:02}.json').exists() for n in range(1,22))
        total += len(files)
    manifest = json.loads((ROOT/'shared/flow-handoff/PROVENANCE.json').read_text())
    for item in manifest['dependencies']:
        assert sha(ROOT/item['source']) == item['sha256'] == sha(ROOT/item['copy'])
        assert item['changed'] is False
    assert sha(ROOT/manifest['fresh_trial']['copy']) == manifest['fresh_trial']['sha256']
    assert sha(ROOT/manifest['fresh_archive']['path']) == manifest['fresh_archive']['sha256']
    # Git identifies changed and new deliverable source files; named PNGs stay untracked.
    raw = subprocess.run(['git','status','--porcelain','-z','--untracked-files=all'],
                         cwd=ROOT,capture_output=True,check=True).stdout
    paths = [item[3:].decode() for item in raw.split(b'\0') if item]
    allowed = ('gathering/','shared/','artifacts/gathering/','dist/')
    assert all(path.startswith(allowed) for path in paths), paths
    oversized = [p for p in paths if not p.startswith('artifacts/')
                 and (ROOT/p).is_file() and (ROOT/p).stat().st_size > 100000]
    assert not oversized, oversized
    tracked = subprocess.run(['git','ls-files','--','artifacts/gathering'],cwd=ROOT,
                             capture_output=True,check=True).stdout
    assert not tracked, 'named artifacts should not be tracked'
    result = {'passed':True,'line_files_unchanged':len(now),
              'record_number':11,'wall_dimensions':[w,h],'wall_format':'RGB PNG',
              'wall_sha256':sha(wall),'jpeg_dimensions':[jw,jh],
              'jpeg_format':'baseline JPEG','gallery_records':total,
              'gallery_bytes':len(page.encode()),'source_paths_in_scope':True,
              'new_nonartifact_files_under_100KB':True,'named_artifacts_untracked':True,
              'provenance_matched':True}
    (ROOT/'gathering/checks/round-11/deliverable.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
