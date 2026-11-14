"""Read-only pixel/header checks for the single Rumi candidate; writes a JSON report."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image

root = Path(__file__).resolve().parents[4]
review = Path(__file__).resolve().parent
source = root / 'art/source/rumi/sol_minimal_v002.aseprite'
output = root / 'art/export/rumi/sol_minimal_v002.png'
data = source.read_bytes()
assert struct.unpack_from('<H', data, 4)[0] == 0xA5E0
frames, width, height, depth = struct.unpack_from('<4H', data, 6)
assert (frames, width, height, depth) == (1, 1254, 1254, 32)
layers = []
offset = 128 + 16
while offset < len(data):
    length, kind = struct.unpack_from('<IH', data, offset)
    assert length >= 6
    if kind == 0x2004:
        name_length = struct.unpack_from('<H', data, offset + 22)[0]
        layers.append(data[offset + 24:offset + 24 + name_length].decode('utf-8'))
    offset += length
assert layers == ['Body - white FFFFFF', 'Eye left - 292733', 'Eye right - 292733']

im = Image.open(output)
assert im.mode == 'RGBA' and im.size == (1254, 1254)
alpha = im.getchannel('A')
bbox = alpha.getbbox()
assert bbox and all((bbox[0] > 0, bbox[1] > 0, bbox[2] < 1254, bbox[3] < 1254))
alpha_counts = Counter(alpha.get_flattened_data())
assert alpha_counts[0] > 0 and alpha_counts[255] > 0
assert sum(count for a, count in alpha_counts.items() if 0 < a < 255) > 0
layer_checks = {}
for suffix, rgb in [('body', (255, 255, 255)), ('eye_left', (41, 39, 51)), ('eye_right', (41, 39, 51))]:
    layer = Image.open(review / f'sol_minimal_v002_{suffix}.png').convert('RGBA')
    visible = Counter(pixel[:3] for pixel in layer.get_flattened_data() if pixel[3])
    assert set(visible) == {rgb}, (suffix, visible)
    layer_checks[suffix] = {'image_size': layer.size, 'visible_rgb': rgb, 'single_flat_rgb': True}

# Only white, charcoal, and their antialiased boundary mixtures may be visible.
for pixel in im.get_flattened_data():
    if not pixel[3]:
        continue
    t = (pixel[0] - 41) / 214
    assert -0.005 <= t <= 1.005
    assert abs(pixel[1] - (39 + 216 * t)) <= 1.1
    assert abs(pixel[2] - (51 + 204 * t)) <= 1.1

report = {
    'source': str(source), 'export': str(output),
    'frames': frames, 'size': [width, height], 'aseprite_color_depth': depth,
    'layers': layers, 'layer_pixel_checks': layer_checks,
    'png_mode': im.mode, 'png_metadata_keys': list(im.info),
    'alpha_bbox_exclusive': bbox,
    'transparent_pixels': alpha_counts[0], 'opaque_pixels': alpha_counts[255],
    'partially_transparent_pixels': sum(n for a, n in alpha_counts.items() if 0 < a < 255),
    'alpha_levels': len(alpha_counts),
    'canvas_border_transparent': True,
    'only_two_role_colors_plus_antialiasing': True,
    'reopened_source_layer_composite_equals_export': 'asserted in Aseprite prepare_v002.lua',
    'visual_review': {
        'single_body_two_eyes_no_accessory': True,
        'no_outline_shading_texture_or_stray_alpha_specks': True,
        'light_and_dark_background_at_256_canvas': 'visually inspected',
        '64_canvas': 'visually inspected; two eyes remain readable',
        'notes': 'White silhouette is naturally lower contrast on light backgrounds; no outline added.'
    },
    'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [source, output]},
}
(review / 'verification_v002.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
