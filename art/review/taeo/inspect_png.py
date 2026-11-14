"""Read-only PNG statistics; preserves generated source files unchanged."""
from collections import Counter
from pathlib import Path
from PIL import Image
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
if len(sys.argv) == 3:
    source = Path(sys.argv[1])
    destination = ROOT / 'art/raw/taeo' / sys.argv[2]
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copy2(source, destination)
else:
    destination = ROOT / 'art/raw/taeo/taeo_neutral_v002.png'

with Image.open(destination) as im:
    alpha = im.getchannel('A')
    print('file:', destination)
    print('size/mode/metadata:', im.size, im.mode, im.info)
    print('alpha range/bounds:', alpha.getextrema(), alpha.getbbox())
    print('alpha counts:', Counter(alpha.get_flattened_data()).most_common(20))
    points = [(0, 0), (512, 100), (512, 350), (512, 600), (512, 900),
              (100, 800), (230, 800), (512, 1480), (300, 900), (400, 900)]
    print('samples:', [(p, im.getpixel(p)) for p in points if p[0] < im.width and p[1] < im.height])
    if im.height > 900:
        print('row900:', [(x, im.getpixel((x, 900))) for x in range(180, min(450, im.width), 5)])
