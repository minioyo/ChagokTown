"""Copy the already inspected geometry helpers into this owned version only."""
import hashlib,json,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for name in ('source','reports','renders','exports','blend'):(ROOT/name).mkdir(exist_ok=True)
source=ART/'town_house_florist_v001/source/geometry.py'
target=ROOT/'source/geometry.py'
if not target.exists():
    text=source.read_text(encoding='utf-8').replace('Geometry helpers derived from cafe v003; independent copy for this asset set.','Geometry helpers copied for the season-one asset set; prior sources stay read-only.')
    target.write_text(text,encoding='utf-8')
access=ROOT/'source/access.py'
if not access.exists():
    source_text=(ART/'town_layout_v003_density/source/build_density.py').read_text(encoding='utf-8')
    tree=ast.parse(source_text);names={'road_candidates','building_bvhs','clear_walk','connection','terrain_bvh','ground'}
    functions=[ast.get_source_segment(source_text,node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    code='"""Inspected local doorway-ray helpers copied from v003; owned season copy."""\nimport bpy,math,heapq\nfrom mathutils import Vector\nfrom mathutils.bvhtree import BVHTree\nfrom scene_common import models_in as model_objects,identity as id_of\n\n'+'\n\n'.join(functions)+'\n'
    code=code.replace("'continuous terrain' in o.name","'terrain' in o.name.lower()")
    access.write_text(code,encoding='utf-8')
folders=['town_layout_v003_density','town_layout_v002_concepts','town_house_florist_v001','town_cafe_v003','town_sol_bakery_bookshop_v001','town_sol_civic_market_workshop_v001']
hashes={str(p.relative_to(ART)):hashlib.sha256(p.read_bytes()).hexdigest() for f in folders for p in (ART/f).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
manifest=ROOT/'reports/protected_art_sha256.json'
if manifest.exists():assert json.loads(manifest.read_text())==hashes,'A protected art input changed'
else:manifest.write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print('Prepared geometry helpers; protected art files:',len(hashes))
