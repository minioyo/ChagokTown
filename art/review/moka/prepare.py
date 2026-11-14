"""Copy generated Moka originals and inspect RGBA; never modify image pixels."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import struct
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
GENERATED = Path('C:/Users/hy/.codex/generated_images/01a1a52f-cd6f-7ea0-a6bd-388b24a8dad8')
SOURCES = {
    'v001': 'exec-f21496e9-83bf-4a4b-85a2-d5e41d17ef1c.png',
    'v002': 'exec-5aefb5da-03db-44b0-a928-65aa72237c93.png',
}


def inspect(path):
    with Image.open(path) as im:
        alpha = im.getchannel('A')
        result = {
            'path': str(path), 'mode': im.mode, 'size': im.size,
            'metadata': {key: repr(value)[:120] for key, value in im.info.items()},
            'alpha_extrema': alpha.getextrema(), 'nonzero_bbox': alpha.getbbox(),
            'alpha_frequencies': Counter(alpha.tobytes()).most_common(16),
            'alpha_bboxes': {str(t): alpha.point(lambda a: 255 if a >= t else 0).getbbox() for t in (1, 16, 64, 128, 200, 240, 250, 254, 255)},
            'samples': {str(xy): im.getpixel(xy) for xy in [(0, 0), (512, 100), (512, 200), (512, 250), (512, 300), (512, 500), (512, 700), (100, 700), (150, 700), (200, 700), (300, 700), (512, 1400), (512, 1500)]},
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


def run_aseprite(script):
    subprocess.run([
        'pwsh', '-NoProfile', '-File', str(ROOT / 'tools/art/aseprite.ps1'),
        '--script', str(ROOT / 'art/review/moka' / script),
    ], cwd=ROOT, check=True)


def verify():
    run_aseprite('verify.lua')
    raw_path = ROOT / 'art/raw/moka/moka_concept_v002.png'
    export_path = ROOT / 'art/export/moka/moka_concept_v002.png'
    source_path = ROOT / 'art/source/moka/moka_concept_v002.aseprite'
    roundtrip_path = ROOT / 'art/review/moka/moka_v002_roundtrip.png'
    with Image.open(raw_path) as raw, Image.open(export_path) as exported, Image.open(roundtrip_path) as reopened:
        same_export = raw.mode == exported.mode and raw.size == exported.size and raw.tobytes() == exported.tobytes()
        same_roundtrip = raw.mode == reopened.mode and raw.size == reopened.size and raw.tobytes() == reopened.tobytes()
        alpha = exported.getchannel('A')
        counts = Counter(alpha.tobytes())
        header = source_path.read_bytes()[:128]
        _, magic, frames, width, height, depth = struct.unpack_from('<I5H', header)
        assert (magic, frames, width, height, depth) == (0xA5E0, 1, 1024, 1536, 32)
        assert same_export and same_roundtrip, 'RGBA pixels changed during export or source reopening'
        assert exported.info.get('srgb') == 0, 'Expected sRGB PNG metadata'
        result = {
            'checked_local_date': '2026-11-04',
            'aseprite_version': '1.3.8.1-dev',
            'canvas': [width, height], 'png_mode': exported.mode,
            'aseprite_color_depth_bits': depth, 'frames': frames,
            'raw_to_export_rgba_identical': same_export,
            'raw_to_reopened_source_rgba_identical': same_roundtrip,
            'raw_metadata': raw.info, 'export_metadata': exported.info,
            'profile_note': 'Raw PNG untagged; interpreted as sRGB. Aseprite adds sRGB tag without changing RGBA bytes.',
            'rgba_sha256': hashlib.sha256(exported.tobytes()).hexdigest(),
            'alpha_extrema': alpha.getextrema(),
            'alpha_zero_pixels': counts[0],
            'alpha_partial_pixels': sum(n for value, n in counts.items() if 0 < value < 255),
            'alpha_opaque_pixels': counts[255],
            'nonzero_alpha_bbox': alpha.getbbox(),
            'alpha_16_or_higher_bbox': alpha.point(lambda a: 255 if a >= 16 else 0).getbbox(),
            'corners_alpha': [alpha.getpixel(xy) for xy in [(0,0),(1023,0),(0,1535),(1023,1535)]],
            'alpha_note': 'Generated interior alpha is mostly 253-254, with faint exterior alpha 1-3. All original alpha values retained; visual composites reviewed separately.',
            'files': {str(p.relative_to(ROOT)): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (raw_path, source_path, export_path, roundtrip_path)},
        }
        report = ROOT / 'art/review/moka/verification_v002.json'
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        coordinates = {
            'outline': (512,250), 'beret_base': (512,300), 'beret_shadow': (665,366),
            'skin_base': (512,700), 'hair_base': (300,700), 'jacket_base': (601,1100),
            'shirt_base': (497,945), 'map_paper': (364,867), 'trousers_base': (430,1175), 'boots_base': (405,1362),
        }
        samples = {
            'status': 'Provisional sampled colors for this concept only; not a project palette or a remapping target.',
            'source': str(export_path.relative_to(ROOT)),
            'note': 'Single sampled pixels; nearby pixels vary. No quantization, recoloring, palette application, or Indexed conversion was performed.',
            'colors': {role: {'position': xy, 'hex': '#%02X%02X%02X' % exported.getpixel(xy)[:3], 'alpha': exported.getpixel(xy)[3]} for role, xy in coordinates.items()},
        }
        (ROOT / 'art/palettes/moka/moka_concept_v002_samples.json').write_text(json.dumps(samples, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(samples, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['minimal-inspect']:
        destination = ROOT / 'art/raw/moka/moka_minimal_neutral_v001.png'
        if not destination.exists():
            shutil.copyfile(GENERATED / 'exec-2c5c6209-d240-4160-8a96-7d9f1afc33be.png', destination)
        with Image.open(destination) as im:
            pixels = list(im.get_flattened_data())
            alpha = im.getchannel('A')
            stats = {
                'mode': im.mode, 'size': im.size, 'metadata': im.info,
                'alpha_extrema': alpha.getextrema(), 'alpha_top': Counter(alpha.tobytes()).most_common(12),
                'alpha_bbox': alpha.getbbox(),
                'visible_bbox': alpha.point(lambda a: 255 if a >= 16 else 0).getbbox(),
                'interior_top_colors': Counter(p[:3] for p in pixels if p[3] >= 240).most_common(12),
                'samples': {str(xy): im.getpixel(xy) for xy in [(640,900),(480,550),(760,580),(350,350),(640,400),(240,500),(1000,500),(100,100)]},
            }
            print(json.dumps(stats, indent=2))
        raise SystemExit(0)
    if sys.argv[1:] == ['export']:
        run_aseprite('export.lua')
        inspect(ROOT / 'art/export/moka/moka_concept_v002.png')
        raise SystemExit(0)
    if sys.argv[1:] == ['verify']:
        verify()
        raise SystemExit(0)
    for version in sys.argv[1:] or SOURCES:
        destination = ROOT / 'art/raw/moka' / f'moka_concept_{version}.png'
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(GENERATED / SOURCES[version], destination)
        inspect(destination)
