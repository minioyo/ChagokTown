"""Read-only pixel checks; only the JSON report is written, never image files."""
from hashlib import sha256
from pathlib import Path
import json
import struct
import sys
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[3]
version = sys.argv[1] if len(sys.argv) > 1 else 'v002'
assert version in ('v002', 'v003', 'v004')
raw_path = ROOT / f'art/raw/rumi/rumi_concept_{version}.png'
export_path = ROOT / f'art/export/rumi/rumi_concept_{version}.png'
source_path = ROOT / f'art/source/rumi/rumi_concept_{version}.aseprite'

def describe(path):
    image = Image.open(path)
    rgba = image.convert('RGBA')
    alpha = rgba.getchannel('A')
    histogram = alpha.histogram()
    return {
        'path': str(path.relative_to(ROOT)), 'mode': image.mode,
        'size': image.size, 'sha256': sha256(path.read_bytes()).hexdigest(),
        'alpha_extrema': alpha.getextrema(), 'alpha_bbox': alpha.getbbox(),
        'alpha_0_pixels': histogram[0], 'alpha_255_pixels': histogram[255],
        'partial_alpha_pixels': sum(histogram[1:255]),
        'alpha_at_least_128_bbox': alpha.point(lambda a: 255 if a >= 128 else 0).getbbox(),
        'corners': [rgba.getpixel(p) for p in [(0,0),(image.width-1,0),(0,image.height-1),(image.width-1,image.height-1)]],
        'metadata': {k: str(v)[:120] for k,v in image.info.items()},
    }

raw = Image.open(raw_path).convert('RGBA')
export = Image.open(export_path).convert('RGBA')
diff = ImageChops.difference(raw, export)
visible_rgb_changes = 0
invisible_rgb_changes = 0
alpha_changes = 0
for before, after in zip(raw.get_flattened_data(), export.get_flattened_data()):
    alpha_changes += before[3] != after[3]
    if before[:3] != after[:3]:
        if before[3] > 0 or after[3] > 0:
            visible_rgb_changes += 1
        else:
            invisible_rgb_changes += 1
header = source_path.read_bytes()[:128]
report = {
    'raw': describe(raw_path), 'export': describe(export_path),
    'comparison': {'same_size': raw.size == export.size,
        'rgba_identical': raw.tobytes() == export.tobytes(),
        'alpha_changed_pixels': alpha_changes,
        'visible_rgb_changed_pixels': visible_rgb_changes,
        'fully_transparent_rgb_changed_pixels': invisible_rgb_changes,
        'max_channel_difference': [pair[1] for pair in diff.getextrema()]},
    'aseprite': {'magic': hex(struct.unpack_from('<H',header,4)[0]),
        'frames': struct.unpack_from('<H',header,6)[0],
        'width': struct.unpack_from('<H',header,8)[0],
        'height': struct.unpack_from('<H',header,10)[0],
        'color_depth_bits': struct.unpack_from('<H',header,12)[0]},
    'review_images': [describe(p) for p in sorted((ROOT/'art/review/rumi').glob(f'rumi_*{version}.png'))],
}
(ROOT/f'art/review/rumi/verification_{version}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'review_images'},indent=2))
print('Review images: ' + str([(r['path'],r['size'],r['alpha_extrema']) for r in report['review_images']]))
