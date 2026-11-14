"""Read-only pixel/file checks for the single Taeo delivery; writes a JSON report."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops

root = Path(__file__).resolve().parents[4]
review = Path(__file__).resolve().parent
stem = 'sol_minimal_neutral_v001'
raw_path = root / 'art/raw/taeo' / (stem + '.png')
png_path = root / 'art/export/taeo' / (stem + '.png')
ase_path = root / 'art/source/taeo' / (stem + '.aseprite')
raw, png = Image.open(raw_path), Image.open(png_path)
body = Image.open(review / (stem + '_body.png'))
eyes = Image.open(review / (stem + '_eyes.png'))
assert raw.mode == png.mode == body.mode == eyes.mode == 'RGBA'
assert raw.size == png.size == body.size == eyes.size == (1254, 1254)
body_rgb, eye_rgb = (91, 134, 175), (23, 45, 66)
assert {p[:3] for p in body.get_flattened_data() if p[3]} == {body_rgb}
assert {p[:3] for p in eyes.get_flattened_data() if p[3]} == {eye_rgb}
assert Counter(body.getchannel('A').get_flattened_data())[255] > 300000
partial_alpha = sum(0 < p[3] < 255 for p in body.get_flattened_data())
assert partial_alpha > 0
assert all(png.getpixel(p)[3] == 0 for p in [(0, 0), (1253, 0), (0, 1253), (1253, 1253)])
bbox = png.getchannel('A').getbbox()
assert abs(bbox[0] - (1254 - bbox[2])) <= 1
assert abs(bbox[1] - (1254 - bbox[3])) <= 1

mask = {(x, y) for y in range(eyes.height) for x in range(eyes.width) if eyes.getpixel((x, y))[3] >= 128}
components = []
while mask:
    seed = mask.pop()
    todo, component = [seed], [seed]
    while todo:
        x, y = todo.pop()
        for q in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]:
            if q in mask:
                mask.remove(q)
                todo.append(q)
                component.append(q)
    components.append([min(p[0] for p in component), min(p[1] for p in component),
                       max(p[0] for p in component)+1, max(p[1] for p in component)+1])
assert len(components) == 2
recomposed = Image.alpha_composite(body, eyes)
extrema = ImageChops.difference(recomposed, png).getextrema()
max_delta = max(v[1] for v in extrema)
assert max_delta <= 1

data = ase_path.read_bytes()
size, magic, frames, width, height, depth = struct.unpack_from('<IHHHHH', data)
assert size == len(data) and magic == 0xA5E0 and (frames, width, height, depth) == (1, 1254, 1254, 32)
frame_size, frame_magic, count = struct.unpack_from('<IHH', data, 128)
assert frame_magic == 0xF1FA
offset, names = 144, []
for _ in range(count):
    chunk_size, chunk_type = struct.unpack_from('<IH', data, offset)
    if chunk_type == 0x2004:
        name_size = struct.unpack_from('<H', data, offset + 6 + 16)[0]
        names.append(data[offset + 24:offset + 24 + name_size].decode('utf-8'))
    offset += chunk_size
assert names == ['Body', 'Eyes']
log = (review / 'aseprite_v001_checks.txt').read_text()
assert 'reopened Aseprite = exported PNG RGBA: PASS' in log
report = {
    'status': 'PASS', 'mode': png.mode, 'canvas': list(png.size),
    'aseprite_depth_bits': depth, 'frames': frames, 'actual_layers': names,
    'candidate_colors': {'body': '#5B86AF', 'eyes': '#172D42'},
    'alpha_bbox_exclusive': list(bbox),
    'margins_LTRB': [bbox[0], bbox[1], 1254-bbox[2], 1254-bbox[3]],
    'eye_components_alpha128': sorted(components),
    'body_partial_alpha_pixels': partial_alpha,
    'alpha_counts': dict(Counter(png.getchannel('A').get_flattened_data()).most_common(8)),
    'png_info': {k: str(v) for k, v in png.info.items()},
    'independent_recomposition_max_channel_delta': max_delta,
    'aseprite_checks': log.strip().splitlines(),
    'sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in [raw_path, ase_path, png_path]},
}
(review / 'verification_v001.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
