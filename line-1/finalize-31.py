"""One-shot media finalization; the generated motif is overwritten by the wall."""
import hashlib
import json
from pathlib import Path
import subprocess


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ffmpeg(args, raw):
    return subprocess.run(['ffmpeg', '-v', 'error', *args], input=raw,
                          capture_output=True, check=True).stdout


def main():
    prior = Path('artifacts/line-1/wall.png').read_bytes()
    record = json.loads(Path('dist/line-1/30.json').read_text())
    assert digest(prior) == record['image'].rsplit('/', 1)[1]
    generated = Path('artifacts/line-1/wall-v12.png').read_bytes()
    old = ffmpeg(['-i', 'pipe:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], prior)
    assert len(old) == 1254 * 1254 * 3
    left, top, width, height = 770, 250, 190, 76
    pigment = ffmpeg(['-i', 'pipe:0', '-vf', 'crop=800:320:220:470,scale=190:76',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], generated)
    assert len(pigment) == width * height * 3
    wall = bytearray(old)
    changed = 0
    for y in range(height):
        for x in range(width):
            p = (y * width + x) * 3
            r, g, b = pigment[p:p+3]
            dark = r < 125 and g < 105 and b < 90
            red = r > g * 1.5 and g < 135 and b < 100 and r < 220
            if not (dark or red):
                continue
            at = ((top + y) * 1254 + left + x) * 3
            tone, strength = ((41, 29, 18), 0.64) if dark else ((149, 65, 28), 0.67)
            for c in range(3):
                wall[at+c] = round(old[at+c] * (1-strength) + tone[c] * strength)
            if wall[at:at+3] != old[at:at+3]:
                changed += 1
    assert changed > 500
    outside = 0
    for y in range(1254):
        for x in range(1254):
            at = (y * 1254 + x) * 3
            if wall[at:at+3] != old[at:at+3] and not (
                    left <= x < left+width and top <= y < top+height):
                outside += 1
    assert outside == 0
    base = ['-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1254x1254', '-i', 'pipe:0']
    png = ffmpeg(base + ['-frames:v', '1', '-c:v', 'png', '-pix_fmt', 'rgb24',
                        '-f', 'image2pipe', 'pipe:1'], wall)
    jpg = ffmpeg(base + ['-vf', 'scale=512:512', '-frames:v', '1', '-c:v', 'mjpeg',
                        '-q:v', '5', '-f', 'image2pipe', 'pipe:1'], wall)
    assert len(jpg) <= 100000
    Path('artifacts/line-1/wall-v12.png').write_bytes(png)
    Path('artifacts/line-1/wall.png').write_bytes(png)
    assert not Path('dist/line-1/31.json').exists()
    Path('dist/line-1/31.jpg').write_bytes(jpg)
    meaning = 'Two ochre stones travel one direct path inside a closed charcoal passage.'
    record = {'name': 'The Sealed Passage',
              'image': 'https://api.imd.fun/artifacts/' + digest(png),
              'attributes': [{'trait_type': k, 'value': v} for k, v in [
                  ('Cave', 'Base'), ('Wall', 'Line 1'), ('Number', 31),
                  ('Left behind', 'transport-check'), ('Meaning', meaning),
                  ('One thing', 'portable live Ethereum state snapshots')]]}
    Path('dist/line-1/31.json').write_text(json.dumps(record, indent=2) + '\n')
    review = {'source_record': 30, 'record_number': 31, 'source_sha256': digest(prior),
              'generated_sha256': digest(generated), 'wall_sha256': digest(png),
              'png_dimensions': [1254, 1254], 'png_format': '8-bit RGB PNG',
              'png_bytes': len(png), 'jpeg_dimensions': [512, 512],
              'jpeg_format': 'baseline JPEG', 'jpeg_bytes': len(jpg),
              'addition_rectangle': [left, top, width, height],
              'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
              'generation_tool': 'installed image.generate_image',
              'visual_review': 'pending final inspection', 'new_hands_or_stencils': 0,
              'unmet_visual_requirements': ['Inherited cave rock is photographic-looking; preserved as required.']}
    Path('line-1/wall-review-31.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
