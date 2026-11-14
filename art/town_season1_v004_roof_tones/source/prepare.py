"""Snapshot immutable predecessors and copy pure readers; never run old drivers."""
from pathlib import Path
import hashlib,json,shutil,ast
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for name in ('exports','blend','reports','renders','renders/whole','renders/models','renders/comparisons'):(ROOT/name).mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths={}
for name in ('town_season1_v001','town_season1_v002_integrated','town_season1_v003_hiddenfaces','audits/2026-11-11_geometry','runtime_samples_v001'):
    for p in (ART/name).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:paths[p.relative_to(ART).as_posix()]=sha(p)
target=ROOT/'reports/protected_inputs.json'
if target.exists():assert all(paths.get(p)==h for p,h in json.loads(target.read_text()).items())
else:target.write_text(json.dumps(paths,indent=2),encoding='utf-8')
for name in ('glb.py','scene_checks.py'):
    target=ROOT/'source'/name
    if not target.exists():shutil.copyfile(ART/'town_season1_v003_hiddenfaces/source'/name,target)
text=(ART/'town_season1_v003_hiddenfaces/source/pixels.py').read_text(encoding='utf-8');tree=ast.parse(text)
functions=[ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('load','png','metrics')]
(ROOT/'source/png_qa.py').write_text('"""Display-code-preserving PNG QA functions copied from v003; no art edits."""\nimport bpy,struct,zlib,binascii,numpy as np\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\n\n'+'\n\n'.join(functions)+'\n',encoding='utf-8')
source=ART/'town_season1_v003_hiddenfaces/reports/manifest.json'
manifest=json.loads(source.read_text())
assert len(manifest['assets'])==36
for row in manifest['assets']:assert sha(ART/row['path'])==row['sha256']
(ROOT/'reports/input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('PROTECTED_INPUTS',len(paths),'INPUTS',len(manifest['assets']))
