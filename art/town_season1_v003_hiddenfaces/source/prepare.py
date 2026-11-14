"""Protect actual inputs and retain the read-only audit algorithms for provenance."""
from pathlib import Path
import hashlib,json,shutil,ast
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for folder in ('exports','blend','renders','renders/whole','renders/models','renders/comparisons','reports','reports/mappings','source/reference'):(ROOT/folder).mkdir(parents=True,exist_ok=True)
manifest=json.loads((ART/'town_season1_v002_integrated/reports/manifest.json').read_text(encoding='utf-8'))
assert len(manifest['assets'])==36 and len({(a['type'],a['level']) for a in manifest['assets']})==36
for a in manifest['assets']:
    assert hashlib.sha256((ART/a['path']).read_bytes()).hexdigest()==a['sha256'],a['path']
    assert (ART/a['editable_blend']).exists()
paths=set()
for folder in ('town_season1_v001','town_season1_v002_integrated','audits/2026-11-11_geometry','runtime_samples_v001'):
    if not (ART/folder).exists():continue
    for p in (ART/folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:paths.add(p)
protected={p.relative_to(ART).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
target=ROOT/'reports/protected_inputs.json'
if target.exists():
    previous=json.loads(target.read_text());assert all(protected.get(p)==h for p,h in previous.items()),'Protected input changed'
else:target.write_text(json.dumps(protected,indent=2),encoding='utf-8')
for name in ('hidden_faces.py','compare_candidates.py'):
    target=ROOT/'source/reference'/(name+'.txt')
    if not target.exists():shutil.copyfile(ART/'audits/2026-11-11_geometry'/name,target)
(ROOT/'reports/input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
source=(ART/'town_season1_v002_integrated/source/town.py').read_text(encoding='utf-8');tree=ast.parse(source)
functions=[ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('hull','local_points','world_xy','footprint','separation')]
(ROOT/'source/spatial.py').write_text('"""Copied read-only spatial checks; no previous driver is imported."""\nimport bpy,math\nfrom mathutils import Vector\n\n'+'\n\n'.join(functions)+'\n',encoding='utf-8')
print('PROTECTED_INPUTS',len(protected))
