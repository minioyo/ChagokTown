"""Read-only shape measurements of the generated minimal mascot."""
from collections import Counter, deque
from pathlib import Path
import json
from PIL import Image

root = Path(__file__).resolve().parents[3]
im = Image.open(root / 'art/raw/taeo/taeo_minimal_neutral_v001.png')
w, h = im.size
pixels = list(im.get_flattened_data())

def components(mask):
    remaining = set(mask)
    result = []
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        found = [start]
        while queue:
            i = queue.popleft()
            x, y = i % w, i // w
            for j in ((i-1 if x else -1), (i+1 if x+1<w else -1),
                      (i-w if y else -1), (i+w if y+1<h else -1)):
                if j in remaining:
                    remaining.remove(j)
                    queue.append(j)
                    found.append(j)
        xs = [i % w for i in found]
        ys = [i // w for i in found]
        result.append({'pixels': len(found), 'bbox': [min(xs), min(ys), max(xs)+1, max(ys)+1]})
    return sorted(result, key=lambda c: c['pixels'], reverse=True)

body = components(i for i, p in enumerate(pixels) if p[3] >= 128)
eyes = components(i for i, p in enumerate(pixels)
                  if p[3] >= 200 and p[0] < 60 and p[1] < 90 and p[2] < 120
                  and 300 < i % w < 950 and 450 < i // w < 700)
report = {'size': im.size, 'body': body[:5], 'eyes': eyes[:5],
          'body_common_rgb': Counter(p[:3] for p in pixels if p[3] >= 250).most_common(8)}
(root / 'art/review/taeo/minimal_generated_measurements.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
