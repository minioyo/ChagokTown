"""Read-only inputs and small, owned copies of inspected helpers."""
import ast,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for folder in ('source','blend','exports','renders','reports'):(ROOT/folder).mkdir(exist_ok=True)
for name in ('geometry.py',):
    target=ROOT/'source'/name
    if not target.exists():target.write_bytes((ART/'town_season1_v001/source'/name).read_bytes())
source=(ART/'town_season1_v001/source/models.py').read_text(encoding='utf-8');tree=ast.parse(source)
needed={'materials','door','facade_window','gable','shell','rose_window','bench'}
target=ROOT/'source/standards.py'
if not target.exists():
    text='"""Metre-scale shared parts copied into the integrated revision."""\nimport bpy,math,json\nfrom pathlib import Path\nfrom mathutils import Vector\nimport geometry as G\nfrom geometry import box,mesh,cyl,rod,ring,ellipsoid,arch\nROOT=Path(__file__).resolve().parents[1]\n\n'
    # facade_window depends on orient_new, not on an old asset's build driver.
    needed.add('orient_new')
    text+='\n\n'.join(ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed)+'\n'
    target.write_text(text,encoding='utf-8')
folders=['town_cafe_v003','town_house_florist_v001','town_sol_bakery_bookshop_v001','town_sol_civic_market_workshop_v001','town_layout_v003_density','town_season1_v001','reference/town_layout_2026_11_09']
hashes={str(p.relative_to(ART)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in folders for p in (ART/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
manifest=ROOT/'reports/protected_art.json'
if manifest.exists():assert json.loads(manifest.read_text())==hashes,'Read-only art input changed'
else:manifest.write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print('Prepared',len(hashes),'read-only art inputs')
