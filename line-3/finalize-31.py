"""Confine an image-tool pigment cutout to vacant rock on round 31's wall.

The cutout is read from stdin and never written as another image. The ancestral
wall is checked against record 30, and every pixel outside the mark rectangle
is retained exactly. This one-time compositor also makes the required JPEG and
record. It does not read environment variables, keys or files outside the repo.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('thumbnail', ROOT / 'gathering/make_thumbnail.py')
thumbnail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thumbnail)


def chunk(tag, body):
    return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body))


def png_rgba(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('image-tool cutout is not PNG')
    position, compressed, header = 8, bytearray(), None
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError('truncated PNG chunk')
        size = int.from_bytes(data[position:position + 4], 'big')
        tag = data[position + 4:position + 8]
        end = position + 12 + size
        if end > len(data):
            raise ValueError('truncated PNG body')
        body = data[position + 8:position + 8 + size]
        if zlib.crc32(tag + body) != int.from_bytes(data[end - 4:end], 'big'):
            raise ValueError('PNG CRC mismatch')
        if tag == b'IHDR':
            header = struct.unpack('>IIBBBBB', body)
        elif tag == b'IDAT':
            compressed.extend(body)
        elif tag == b'IEND':
            break
        position = end
    if header is None:
        raise ValueError('missing PNG header')
    width, height, depth, color, compression, filtering, interlace = header
    if (width > 4096 or height > 4096 or depth != 8 or color != 6 or
            compression or filtering or interlace):
        raise ValueError('requires noninterlaced 8-bit RGBA cutout at most 4096px')
    stride = 4 * width
    raw = zlib.decompress(compressed)
    if len(raw) != (stride + 1) * height:
        raise ValueError('PNG data size mismatch')
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        mode = raw[start]
        row = bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = row[i - 4] if i >= 4 else 0
            b = previous[i]
            c = previous[i - 4] if i >= 4 else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = a
            elif mode == 2:
                predictor = b
            elif mode == 3:
                predictor = (a + b) // 2
            elif mode == 4:
                estimate = a + b - c
                da, db, dc = abs(estimate - a), abs(estimate - b), abs(estimate - c)
                predictor = a if da <= db and da <= dc else (b if db <= dc else c)
            else:
                raise ValueError('invalid PNG filter')
            row[i] = (row[i] + predictor) & 255
        rows.append(bytes(row))
        previous = row
    return width, height, rows


def encode_rgb(width, height, rows):
    body = zlib.compress(b''.join(b'\0' + bytes(row) for row in rows), 9)
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', body) + chunk(b'IEND', b''))


def main():
    old_path = ROOT / 'artifacts/line-3/wall.png'
    previous = old_path.read_bytes()
    previous_hash = hashlib.sha256(previous).hexdigest()
    prior_record = json.loads((ROOT / 'dist/line-3/30.json').read_text())
    assert previous_hash == prior_record['image'].rsplit('/', 1)[1]
    width, height, ancestors = thumbnail.png_rgb(previous)
    assert (width, height) == (1254, 1254)
    cutout = sys.stdin.buffer.read(8 * 1024 * 1024 + 1)
    if len(cutout) > 8 * 1024 * 1024:
        raise ValueError('cutout exceeds 8 MiB')
    sw, sh, source = png_rgba(cutout)

    # Open stone on the lower right, clear of the scroll and inherited pod.
    box = (1025, 785, 1165, 885)
    x0, y0, x1, y1 = box
    target_w, target_h = x1 - x0, y1 - y0
    rows = [bytearray(row) for row in ancestors]
    changed = 0
    alpha_samples = 0
    for dy in range(target_h):
        sy0, sy1 = dy * sh // target_h, (dy + 1) * sh // target_h
        for dx in range(target_w):
            sx0, sx1 = dx * sw // target_w, (dx + 1) * sw // target_w
            red = green = blue = alpha = 0
            count = (sy1 - sy0) * (sx1 - sx0)
            for sy in range(sy0, sy1):
                row = source[sy]
                for sx in range(sx0, sx1):
                    r, g, b, a = row[4 * sx:4 * sx + 4]
                    alpha += a
                    red += r * a
                    green += g * a
                    blue += b * a
            if alpha == 0:
                continue
            # Scale alpha down so the pigment remains worn on the ancestral rock.
            opacity = min(180, alpha // count * 3 // 4)
            if opacity < 10:
                continue
            pigment = (red // alpha, green // alpha, blue // alpha)
            at = 3 * (x0 + dx)
            old = rows[y0 + dy][at:at + 3]
            new = bytes((old[c] * (255 - opacity) + pigment[c] * opacity + 127) // 255
                        for c in range(3))
            if new != old:
                rows[y0 + dy][at:at + 3] = new
                changed += 1
                alpha_samples += alpha
    assert changed > 1000, changed
    outside = sum(rows[y][3*x:3*x+3] != ancestors[y][3*x:3*x+3]
                  for y in range(height) for x in range(width)
                  if not (x0 <= x < x1 and y0 <= y < y1))
    assert outside == 0
    png = encode_rgb(width, height, rows)
    assert thumbnail.png_rgb(png)[2] == [bytes(row) for row in rows]
    jpeg = thumbnail.jpeg(thumbnail.resize(width, height, rows))
    assert len(jpeg) < 100000
    new_hash = hashlib.sha256(png).hexdigest()
    meaning = 'Three worn stones let Pepe see each separate word in a message.'
    record = {'name': 'Words in Stone',
              'image': 'https://api.imd.fun/artifacts/' + new_hash,
              'attributes': [{'trait_type': key, 'value': value} for key, value in [
                  ('Cave', 'Base'), ('Wall', 'Line 3'), ('Number', 31),
                  ('Left behind', 'calldata-words'), ('Meaning', meaning),
                  ('One thing', 'Offline EIP-1559 transaction decoding')]]}
    (ROOT / 'artifacts/line-3/wall-v12.png').write_bytes(png)
    old_path.write_bytes(png)
    (ROOT / 'dist/line-3/31.jpg').write_bytes(jpeg)
    (ROOT / 'dist/line-3/31.json').write_text(json.dumps(record, indent=2) + '\n')
    review = {'wall': {'paths': ['artifacts/line-3/wall-v12.png',
                                 'artifacts/line-3/wall.png'],
                       'width': width, 'height': height, 'format': 'PNG',
                       'mode': 'RGB', 'bytes': len(png), 'sha256': new_hash},
              'thumbnail': {'path': 'dist/line-3/31.jpg', 'width': 512,
                            'height': 512, 'format': 'JPEG', 'bytes': len(jpeg)},
              'preservation': {'inheritedSha256': previous_hash,
                               'editRectangleXYXY': list(box),
                               'changedPixels': changed,
                               'changedPixelsOutsideRectangle': outside},
              'cutout': {'width': sw, 'height': sh, 'format': 'PNG',
                         'mode': 'RGBA', 'alphaSum': alpha_samples},
              'visualReview': {'reviewed': False},
              'unmetVisualRequirements': ['Visual review pending']}
    (ROOT / 'line-3/round-31-review.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
