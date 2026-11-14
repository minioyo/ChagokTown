"""Inspect the new PNG and report the intentional Aseprite framing operation."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
raw_path = ROOT / 'art/raw/taeo/taeo_neutral_v003.png'
png_path = ROOT / 'art/export/taeo/taeo_neutral_v003.png'
source_path = ROOT / 'art/source/taeo/taeo_neutral_v003.aseprite'
reference_path = ROOT / 'art/reference/shared/user_style_1000023405.jpg'
raw = Image.open(raw_path)
png = Image.open(png_path)
assert raw.mode == png.mode == 'RGBA' and raw.size == png.size == (1024, 1536)
magic, frames, width, height, depth = struct.unpack_from('<5H', source_path.read_bytes(), 4)
assert magic == 0xA5E0 and frames == 1 and (width, height, depth) == (1024, 1536, 32)
alpha = png.getchannel('A')
counts = Counter(alpha.get_flattened_data())
assert alpha.getextrema()[0] == 0 and len(counts) > 2 and 'srgb' in png.info
log = (ROOT / 'art/review/taeo/aseprite_v003_checks.txt').read_text(encoding='utf-8')
assert 'RGBA after framing = reopened Aseprite = exported PNG: PASS' in log
old_report = json.loads((ROOT / 'art/review/taeo/verification_v002.json').read_text(encoding='utf-8'))
assert all(sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in old_report['sha256'].items())
samples = {}
for name, point in {
    'hair': (500, 125), 'skin': (520, 255), 'iris': (478, 230),
    'hoodie': (430, 530), 'headphones': (470, 385),
    'trousers': (420, 1000), 'shoes': (370, 1460)
}.items():
    placed = (round(point[0] * 0.875 + 64), round(point[1] * 0.875 + 96))
    rgba = png.getpixel(placed)
    samples[name] = {'raw_xy': point, 'export_xy': placed,
                     'rgba': rgba, 'hex_rgb': '#%02X%02X%02X' % rgba[:3]}
report = {
    'raw': str(raw_path.relative_to(ROOT)),
    'export': str(png_path.relative_to(ROOT)),
    'source': str(source_path.relative_to(ROOT)),
    'size': png.size, 'png_mode': png.mode, 'source_depth_bits': depth,
    'intentional_framing': {'scale': 0.875, 'method': 'Aseprite bilinear', 'offset_xy': [64, 96]},
    'raw_export_rgba_equal': raw.tobytes() == png.tobytes(),
    'framed_source_reopen_export_rgba_equal': True,
    'aseprite_evidence': log.strip(), 'v002_preserved_sha256': True,
    'alpha_range': alpha.getextrema(), 'distinct_alpha_values': len(counts),
    'fully_transparent_pixels': counts[0], 'fully_opaque_pixels': counts[255],
    'partly_transparent_pixels': sum(v for a, v in counts.items() if 0 < a < 255),
    'alpha_counts_top': counts.most_common(6),
    'alpha_bounds': {str(t): alpha.point(lambda a, t=t: 255 if a >= t else 0).getbbox() for t in (1, 8, 128, 250)},
    'corner_alpha': [alpha.getpixel(p) for p in ((0, 0), (1023, 0), (0, 1535), (1023, 1535))],
    'png_metadata_keys': list(png.info), 'color_samples': samples,
    'sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
               for p in (raw_path, source_path, png_path, reference_path)},
}
(ROOT / 'art/review/taeo/verification_v003.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
