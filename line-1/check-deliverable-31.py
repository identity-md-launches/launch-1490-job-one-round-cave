"""Read-only source, metadata, media and regression verification for round 31."""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def command(args, raw=None):
    return subprocess.run(args, input=raw, capture_output=True, check=True).stdout


def main():
    goal = Path('line-1/GOAL.md').read_bytes()
    assert goal == command(['git', 'show', 'HEAD:line-1/GOAL.md'])
    records = sorted(Path('dist/line-1').glob('[0-9][0-9].json'))
    assert len(records) == 31 and records[-1].name == '31.json'
    record = json.loads(records[-1].read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    attrs = record['attributes']
    assert [a['trait_type'] for a in attrs] == [
        'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing']
    assert all(set(a) == {'trait_type', 'value'} for a in attrs)
    assert [a['value'] for a in attrs[:4]] == ['Base', 'Line 1', 31, 'transport-check']
    assert type(attrs[2]['value']) is int
    wall = Path('artifacts/line-1/wall-v12.png').read_bytes()
    assert wall == Path('artifacts/line-1/wall.png').read_bytes()
    sha = hashlib.sha256(wall).hexdigest()
    assert record['image'] == 'https://api.imd.fun/artifacts/' + sha
    media = []
    for name, dimensions, codec in [
        ('artifacts/line-1/wall-v12.png', [1254, 1254], 'png'),
        ('dist/line-1/31.jpg', [512, 512], 'mjpeg'),
    ]:
        data = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                  '-show_entries', 'stream=width,height,codec_name,pix_fmt',
                                  '-of', 'json', name]))['streams'][0]
        assert [data['width'], data['height']] == dimensions
        assert data['codec_name'] == codec
        decoded = command(['ffmpeg', '-v', 'error', '-i', name, '-f', 'rawvideo',
                           '-pix_fmt', 'rgb24', 'pipe:1'])
        assert len(decoded) == dimensions[0] * dimensions[1] * 3
        media.append({'path': name, 'dimensions': dimensions, 'format': codec,
                      'bytes': Path(name).stat().st_size, 'decoded': True})
    assert Path('dist/line-1/31.jpg').stat().st_size <= 100000
    changed = command(['git', 'diff', '--name-only']).decode().splitlines()
    untracked = command(['git', 'ls-files', '--others', '--exclude-standard']).decode().splitlines()
    for name in changed + untracked:
        assert name.startswith('line-1/') or name in ['dist/line-1/31.json', 'dist/line-1/31.jpg'], name
        assert Path(name).stat().st_size <= 100000
    assert not any(name.startswith('dist/') for name in changed)
    command(['git', 'diff', '--check'])
    assert not command(['git', 'ls-files', 'artifacts/line-1', 'dist/line-1/31.jpg',
                        'dist/line-1/31.json'])
    demo = json.loads(command(['python3', '-B', 'line-1/tools/transport-check/transport_check.py', 'demo']))
    assert demo['status'] == 'passed' and demo['network_used'] is False
    Path('line-1/tools/transport-check/check-results.json').write_text(json.dumps(demo, indent=2) + '\n')
    tests = []
    for path in sorted(Path('line-1/tools').glob('*/test*.py')):
        run = subprocess.run(['python3', '-B', str(path)], capture_output=True, text=True, timeout=120)
        assert run.returncode == 0, run.stdout + run.stderr
        count = int(re.search(r'Ran (\d+) tests?', run.stdout + run.stderr).group(1))
        tests.append({'test': str(path), 'exit_code': run.returncode,
                      'test_count': count, 'output': run.stdout + run.stderr})
    Path('line-1/tools/transport-check/regression-results.json').write_text(json.dumps(tests, indent=2) + '\n')
    command(['python3', '-B', 'line-1/tools/snapshot-check/check_snapshot.py'],
            Path('line-1/tools/transport-check/live-zto.json').read_bytes())
    review = json.loads(Path('line-1/wall-review-31.json').read_text())
    assert review['wall_sha256'] == sha and review['changed_pixels_outside_rectangle'] == 0
    result = {'status': 'passed', 'goal_unchanged': True, 'older_records_unchanged': True,
              'scope_checked': True, 'media': media, 'record': 'dist/line-1/31.json',
              'wall_sha256': sha, 'offline_transport_checks': demo['checks_passed'],
              'ancestor_suites': len(tests), 'ancestor_tests': sum(t['test_count'] for t in tests),
              'outputs_untracked': True,
              'unmet_visual_requirements': review['unmet_visual_requirements']}
    Path('line-1/submission-check-31.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
