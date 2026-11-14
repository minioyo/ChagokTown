"""Read the exact source components, color roles and optimized accessor formats."""
import bpy,sys,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
manifest=json.loads((ROOT/'reports/input_manifest.json').read_text());loaded=None;report={}
for row in manifest['assets']:
    blend=F.ART/row['editable_blend']
    if loaded!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend));loaded=blend
    scene=bpy.data.scenes[row['editable_scene']];parts=collections.Counter()
    for obj in scene.objects:
        if obj.type=='MESH' and ('roof' in obj.name.lower() or 'tile' in obj.name.lower()):
            role=obj.name.split('.')[0];m=obj.data.materials[0] if obj.data.materials else None
            parts[role,m.name if m else None,tuple(m.diffuse_color) if m else ()]+=1
    doc,blob,_=F.read(F.ART/row['path']);p=F.primitive(doc);ca=doc['accessors'][p['attributes']['COLOR_0']]
    key=f"{row['type']}_level_{row['level']}"
    report[key]={'parts':[{'role':k[0],'material':k[1],'linear_rgba':k[2],'count':n} for k,n in sorted(parts.items())],
                 'color_accessor':ca,'colors':sorted(set(F.accessor(doc,blob,p['attributes']['COLOR_0'])))}
    print(key,json.dumps(report[key]['parts']),flush=True)
(ROOT/'reports/roof_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8');F.protect()
