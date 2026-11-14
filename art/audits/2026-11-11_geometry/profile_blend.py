"""Inspect editable component costs and in-memory bevel experiments; never save inputs."""
from pathlib import Path
import bpy, json, hashlib, collections

OUT=Path(__file__).resolve().parent;PROJECT=OUT.parents[2];ART=PROJECT/'art'
manifest=json.loads((ART/'town_season1_v002_integrated/reports/manifest.json').read_text())
inputs=[ART/'town_season1_v002_integrated/blend/integrated_models.blend',
        ART/'town_season1_v001/blend/season1_models.blend',
        ART/'town_season1_v002_integrated/blend/integrated_village.blend']
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
report={'models':{},'environment':{},'input_blends_unchanged':False,
        'experiment':'Disable bevel only on thin box-like components in memory. Counts only; not approved assets.'}

def evaluate(o,dg):
    evaluated=o.evaluated_get(dg);me=evaluated.to_mesh();me.calc_loop_triangles()
    result={'triangles':len(me.loop_triangles),'mesh_vertices':len(me.vertices)}
    evaluated.to_mesh_clear();return result

for blend in inputs[:2]:
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    for asset in [a for a in manifest['assets'] if ART/a['editable_blend']==blend]:
        scene=bpy.data.scenes[asset['editable_scene']];bpy.context.window.scene=scene;bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();parts=[];candidates=[]
        for o in scene.objects:
            if o.type!='MESH' or o.name.lower().startswith(('studio','backdrop','floor')):continue
            if not o.modifiers and len(o.data.vertices)>2000:continue
            stat=evaluate(o,dg)
            group=o.name.split(' • ')[0].split(' · ')[0]
            bevels=[m for m in o.modifiers if m.type=='BEVEL' and m.show_viewport]
            dims=[max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in range(3)]
            # Eight-vertex boxes: suppress only sub-6cm edge rounding, not roof masses/arches.
            thin=(len(o.data.vertices)==8 and min(dims)<=.0601 and max(dims)>=.2 and bevels)
            entry={'name':o.name,'category':group,**stat,'thin_bevel_candidate':bool(thin),
                   'bevel_segments':[m.segments for m in bevels]}
            parts.append(entry)
            if thin:
                for m in bevels:m.show_viewport=False
                candidates.append((o,bevels,entry))
        bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        reduction=0
        for o,mods,entry in candidates:
            after=evaluate(o,dg);entry['without_thin_bevel_triangles']=after['triangles']
            reduction+=entry['triangles']-after['triangles']
            for m in mods:m.show_viewport=True
        bpy.context.view_layer.update()
        grouped=collections.Counter()
        for p in parts:grouped[p['category']]+=p['triangles']
        key=f"{asset['type']}_level_{asset['level']}"
        report['models'][key]={'triangles':sum(p['triangles'] for p in parts),
                              'thin_bevel_candidate_count':len(candidates),'thin_bevel_triangles_saved':reduction,
                              'categories':dict(grouped.most_common()),'parts':parts}
        print('PROFILED',key,report['models'][key]['triangles'],reduction,flush=True)

bpy.ops.wm.open_mainfile(filepath=str(inputs[2]))
report['map_scene_names']=[s.name for s in bpy.data.scenes]
scenes=[s for s in bpy.data.scenes if 'final' in s.name.lower()]
assert scenes,'Missing final scene'
scene=scenes[0];bpy.context.window.scene=scene;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
parts=[]
for inst in dg.object_instances:
    if inst.object.type!='MESH':continue
    o=inst.object;me=o.to_mesh();me.calc_loop_triangles()
    parts.append({'name':o.name,'is_instance':inst.is_instance,'triangles':len(me.loop_triangles),
                  'mesh_vertices':len(me.vertices),'materials':len(me.materials)})
    o.to_mesh_clear()
report['environment']={'scene':scene.name,'total_scene_triangles':sum(p['triangles'] for p in parts),
                       'evaluated_mesh_instances':len(parts),'parts':sorted(parts,key=lambda p:p['triangles'],reverse=True)}
for level in (1,2,3):
    used=[report['models'][f"{p['kind']}_level_{level}"] for p in manifest['layout']]
    report.setdefault('fourteen_plot_bevel_experiment',{})[str(level)]={
        'before_triangles':sum(x['triangles'] for x in used),
        'candidate_triangles_saved':sum(x['thin_bevel_triangles_saved'] for x in used)}
report['input_blends_unchanged']=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
assert report['input_blends_unchanged']
(OUT/'component_profile.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PROFILE_COMPLETE',report['fourteen_plot_bevel_experiment'],report['environment']['total_scene_triangles'],flush=True)
