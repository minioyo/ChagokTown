"""Read-only pixel checks for Moka sol_minimal v001; also preserve the generator PNG."""
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import shutil
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
NAME = "sol_minimal_neutral_v001"
RAW = ROOT / "art/raw/moka" / (NAME + ".png")
GENERATED = Path(r"C:\Users\hy\.codex\generated_images\01a1a54b-a95d-7b41-9d4c-c858c19c4ee9\exec-8eda3033-56dd-4add-948e-1a5e5903fd00.png")
if not RAW.exists():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GENERATED, RAW)


def describe(path):
    im = Image.open(path).convert("RGBA")
    colors = Counter(im.get_flattened_data())
    alpha = im.getchannel("A")
    return {
        "file": str(path.relative_to(ROOT)),
        "size": list(im.size),
        "mode": Image.open(path).mode,
        "png_color_metadata": {k: len(v) if isinstance(v, bytes) else v for k, v in Image.open(path).info.items()},
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "alpha_bbox": alpha.getbbox(),
        "alpha_zero": sum(n for p, n in colors.items() if p[3] == 0),
        "alpha_partial": sum(n for p, n in colors.items() if 0 < p[3] < 255),
        "alpha_opaque": sum(n for p, n in colors.items() if p[3] == 255),
        "most_common_rgba": colors.most_common(5),
        "opaque_rgb_count": len({p[:3] for p in colors if p[3] == 255}),
    }


raw = Image.open(RAW).convert("RGBA")
w, h = raw.size
rgba = list(raw.get_flattened_data())
mask = bytearray(p[3] >= 128 for p in rgba)
components = []
for start in range(w * h):
    if not mask[start]:
        continue
    mask[start] = 0
    queue = deque([start])
    points = []
    while queue:
        i = queue.popleft()
        points.append(i)
        x, y = i % w, i // w
        adjacent = []
        if x: adjacent.append(i - 1)
        if x + 1 < w: adjacent.append(i + 1)
        if y: adjacent.append(i - w)
        if y + 1 < h: adjacent.append(i + w)
        for j in adjacent:
            if mask[j]:
                mask[j] = 0
                queue.append(j)
    components.append(points)
main = max(components, key=len)
report = {
    "raw": describe(RAW),
    "raw_component_count_alpha128": len(components),
    "raw_largest_component_pixels": len(main),
    "raw_largest_component_bbox": [min(i % w for i in main), min(i // w for i in main), max(i % w for i in main) + 1, max(i // w for i in main) + 1],
    "raw_rows": {str(y): [min(i % w for i in main if i // w == y), max(i % w for i in main if i // w == y)] for y in [320, 350, 400, 450, 500, 600, 700, 800, 900, 950, 970]},
}
for side, lo, hi in [("left", 0, w // 2), ("right", w // 2, w)]:
    eye = [i for i in main if lo <= i % w < hi and rgba[i][0] < 130]
    report["raw_" + side + "_eye_bbox"] = [min(i % w for i in eye), min(i // w for i in eye), max(i % w for i in eye) + 1, max(i // w for i in eye) + 1]
    report["raw_" + side + "_eye_color"] = Counter(rgba[i] for i in eye).most_common(1)

output = ROOT / "art/export/moka" / (NAME + ".png")
roundtrip = ROOT / "art/review/moka/sol_minimal" / (NAME + "_roundtrip.png")
if output.exists():
    source = ROOT / "art/source/moka" / (NAME + ".aseprite")
    data = source.read_bytes()
    magic, frames, width, height, depth = struct.unpack_from("<5H", data, 4)
    assert magic == 0xA5E0 and (frames, width, height, depth) == (1, w, h, 32)
    offset = 144  # First frame's chunks follow the 128-byte file + 16-byte frame header.
    color_profile_type = None
    while offset < len(data):
        length, chunk_type = struct.unpack_from("<IH", data, offset)
        assert length >= 6
        if chunk_type == 0x2007:
            color_profile_type = struct.unpack_from("<H", data, offset + 6)[0]
        offset += length
    assert color_profile_type == 1, "Saved Aseprite profile must be sRGB"
    report["aseprite_header"] = {"frames": frames, "width": width, "height": height, "depth": depth, "color_profile_type": color_profile_type}
    assert RAW.read_bytes() == GENERATED.read_bytes(), "Generated original was not preserved"
    report["raw_copy_byte_equal"] = True
    report["export"] = describe(output)
    exported = Image.open(output).convert("RGBA")
    assert exported.size == raw.size
    assert exported.getpixel((0, 0))[3] == 0
    assert report["export"]["alpha_partial"] > 0
    assert report["export"]["alpha_opaque"] > 0
    if roundtrip.exists():
        reopened = Image.open(roundtrip).convert("RGBA")
        assert exported.tobytes() == reopened.tobytes(), "Aseprite roundtrip pixels changed"
        report["roundtrip_rgba_equal"] = True
    for layer in ["body", "eyes"]:
        path = ROOT / "art/review/moka/sol_minimal" / (NAME + "_" + layer + ".png")
        if path.exists():
            report[layer + "_layer"] = describe(path)
            pixels = Image.open(path).convert("RGBA").get_flattened_data()
            rgb = {p[:3] for p in pixels if p[3] > 0}
            expected = (217, 117, 101) if layer == "body" else (49, 38, 41)
            assert rgb == {expected}, (layer, rgb)
            report[layer + "_visible_rgb_exact"] = True
    report["checks_passed"] = True
    (ROOT / "art/review/moka/sol_minimal/verification_v001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
