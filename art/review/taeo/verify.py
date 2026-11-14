"""Read-only image validation; writes only the resulting JSON report."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
raw_path = ROOT / 'art/raw/taeo/taeo_neutral_v002.png'
png_path = ROOT / 'art/export/taeo/taeo_neutral_v002.png'
source_path = ROOT / 'art/source/taeo/taeo_neutral_v002.aseprite'
raw = Image.open(raw_path)
png = Image.open(png_path)
assert raw.mode == png.mode == 'RGBA'
assert raw.size == png.size == (1024, 1536)
raw_pixels = list(raw.get_flattened_data())
out_pixels = list(png.get_flattened_data())
alpha = png.getchannel('A')
counts = Counter(alpha.get_flattened_data())
visible_changes = sum(a != b for a, b in zip(raw_pixels, out_pixels) if a[3] or b[3])
alpha_changes = sum(a[3] != b[3] for a, b in zip(raw_pixels, out_pixels))
hidden_rgb_changes = sum(a[:3] != b[:3] for a, b in zip(raw_pixels, out_pixels) if a[3] == b[3] == 0)
header = source_path.read_bytes()[:128]
magic, frames, width, height, depth = struct.unpack_from('<5H', header, 4)
assert magic == 0xA5E0 and frames == 1 and (width, height, depth) == (1024, 1536, 32)
assert alpha_changes == 0 and visible_changes == 0
report = {
    'raw': str(raw_path.relative_to(ROOT)),
    'export': str(png_path.relative_to(ROOT)),
    'source': str(source_path.relative_to(ROOT)),
    'size': list(png.size),
    'png_mode': png.mode,
    'aseprite_header': {'frames': frames, 'width': width, 'height': height, 'color_depth_bits': depth},
    'alpha_range': list(alpha.getextrema()),
    'alpha_changed_pixels': alpha_changes,
    'visible_rgba_changed_pixels': visible_changes,
    'fully_transparent_rgb_changed_pixels': hidden_rgb_changes,
    'all_rgba_bytes_equal': raw.tobytes() == png.tobytes(),
    'fully_transparent_pixels': counts[0],
    'partly_transparent_pixels': sum(v for a, v in counts.items() if 0 < a < 255),
    'fully_opaque_pixels': counts[255],
    'distinct_alpha_values': len(counts),
    'alpha_bounds': {str(t): alpha.point(lambda a, t=t: 255 if a >= t else 0).getbbox() for t in (1, 8, 128, 250)},
    'corner_alpha': [alpha.getpixel(p) for p in ((0, 0), (1023, 0), (0, 1535), (1023, 1535))],
    'png_metadata_keys': list(png.info),
    'sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in (raw_path, source_path, png_path)},
    'color_samples': {name: {'xy': point, 'rgba': png.getpixel(point)} for name, point in {
        'hair': (512, 350), 'skin': (512, 600), 'hoodie': (400, 900),
        'headphone': (460, 790), 'trousers': (580, 1220), 'shoes': (410, 1420),
        'outline': (320, 900)
    }.items()},
}
destination = ROOT / 'art/review/taeo/verification_v002.json'
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
