"""Normalize the eight inherited types without scaling people-sized details."""
import bpy,bmesh,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import geometry as G
import standards as S
import town as T
bpy.ops.wm.read_factory_settings(use_empty=True)
library=bpy.context.scene;library.name='LIBRARY • twenty-four normalized assets';G.scene=library
palette=S.materials();doors=[];windows=[]

def door(x,y):
    doors.append({'xy':[x,y],'panel_width':.8,'panel_height':1.6,'bottom':.16})
    S.door(x,y)

def window(x,y,z,w,h,trim='Cream',cross=True):
    windows.append({'xyz':[x,y,z],'width':w,'height':h})
    G.box('Window • opaque blue glazing',(x,y-.06,z),(w,.06,h),'Glass',0)
    for dx in (-w/2,w/2):G.box('Window • butt-jointed jamb',(x+dx,y-.11,z),(.085,.12,h-.085),trim,0)
    for dz in (-h/2,h/2):G.box('Window • butt-jointed lintel',(x,y-.11,z+dz),(w+.085,.12,.085),trim,0)
    G.box('Window • centre mullion',(x,y-.135,z),(.05,.08,h-.085),trim,0)
    if cross:G.box('Window • crossbar',(x,y-.155,z+.07),(w-.085,.045,.05),trim,0)
    G.box('Window • deep sill',(x,y-.18,z-h/2-.065),(w+.22,.27,.12),'Cream',.018)

G.door=door;G.window=window
import legacy_cafe as C
import legacy_homes as H
import legacy_shops as B
import legacy_civic as V
BUILDERS={'cafe':lambda n:C.build(n,True),'house':lambda n:H.house(n,True),'florist':lambda n:H.florist(n,True),
 'bakery':B.bakery,'bookshop':B.bookshop,'town_hall':V.town_hall,'grocer':V.grocer,'workshop':V.workshop}

def recolor(coll,kind,level):
    for o in coll.objects:
        if o.type!='MESH':continue
        for slot in o.material_slots:
            if kind=='bakery' and ('Roof' in o.name or 'roof' in o.name):
                if slot.material==G.M['Clay']:slot.material=G.M['Roof olive']
                elif slot.material==G.M['Clay light']:slot.material=G.M['Roof olive light']
            if kind=='bookshop':
                if slot.material==G.M['Sage']:slot.material=G.M['Warm plaster']
                if any(s in o.name for s in ('Roof','roof','Gable')):
                    if slot.material in (G.M['Teal'],G.M['Teal dark']):slot.material=G.M['Roof slate']
                    elif slot.material==G.M['Teal light']:slot.material=G.M['Roof slate light']
    if kind=='bookshop' and level==3:
        G.box('Lookout • warm plaster shaft',(.83,.25,5.4),(.75,.77,2.22),'Warm plaster',.025)
        G.box('Lookout • pale cornice',(.83,.25,6.49),(.90,.92,.14),'Stone light',.015)
        x=.83;y=.25;z=6.56;r=.535
        vs=[(x-r,y-r,z),(x+r,y-r,z),(x+r,y+r,z),(x-r,y+r,z),(x,y,7.4)]
        G.mesh('Lookout • closed pointed slate cap',vs,[(3,2,1,0),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Roof slate',0)
        S.facade_window(.83,-.16,5.18,.46,.72)
        S.facade_window(1.22,.25,5.38,.46,.72,math.pi/2)

def check(coll):
    dg=bpy.context.evaluated_depsgraph_get();count=0
    for o in coll.objects:
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
        assert all(t.area>1e-12 for t in me.loop_triangles),(o.name,'degenerate')
        assert all(math.isfinite(c) and abs(n.vector.length-1)<.001 for n in me.corner_normals for c in n.vector),(o.name,'normal')
        bm=bmesh.new();bm.from_mesh(me)
        assert all(e.is_manifold and e.is_contiguous for e in bm.edges),(o.name,'open/inconsistent')
        assert bm.calc_volume(signed=True)>1e-10,(o.name,'inward')
        bm.free();e.to_mesh_clear();count+=1
    return {'closed_outward_components':count,'degenerate_triangles':0,'finite_unit_normals':True}

report={'models':{},'generic_door_panel_m':[.8,1.6],'ordinary_floor_pitch_m':2.0,'world_scale':1.0,'unchanged_types':list(T.NEW)}
for kind,fn in BUILDERS.items():
    for level in (1,2,3):
        key=f'{kind}_level_{level}';scene=bpy.data.scenes.new('EDIT • '+key);scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;bpy.context.window.scene=scene;G.scene=scene
        doors.clear();windows.clear();coll,root=fn(level);recolor(coll,kind,level);bpy.context.view_layer.update()
        checks=check(coll);edit=G.stats(coll)
        low=G.collection('RUNTIME • '+key);lr=root.copy();low.objects.link(lr)
        for source in list(coll.objects):
            if source.type!='MESH':continue
            o=source.copy();o.data=source.data.copy();low.objects.link(o);o.parent=lr
        obj=G.consolidate(low,lr,key,level);obj['door_panel_standard_m']=[.8,1.6];obj['floor_pitch_m']=2.
        runtime=G.stats(low);assert abs(runtime['bounds_min'][2])<1e-5,(key,runtime['bounds_min'])
        assert runtime['triangles']<={1:4000,2:6000,3:8000}[level],(key,runtime['triangles'])
        report['models'][key]={'type':kind,'level':level,'editable':edit,'runtime':runtime,'source_checks':checks,'doors':list(doors),'window_calls':list(windows)}
        scene.collection.children.unlink(low);library.collection.children.link(low)
        T.configure(scene,True) if scene.camera else None
        print('NORMALIZED',key,runtime['triangles'],flush=True)

# One envelope per type covers all three growth stages, including props and roofs.
report['max_stage_bounds']={}
for kind in BUILDERS:
    rows=[report['models'][f'{kind}_level_{n}']['runtime'] for n in (1,2,3)]
    lo=[min(r['bounds_min'][i] for r in rows) for i in range(2)];hi=[max(r['bounds_max'][i] for r in rows) for i in range(2)]
    report['max_stage_bounds'][kind]={'min':lo,'max':hi}
    for level in (1,2,3):
        key=f'{kind}_level_{level}';bpy.context.window.scene=library;coll=bpy.data.collections['RUNTIME • '+key]
        obj=next(o for o in coll.objects if o.type=='MESH');obj['placement_xy_min']=lo;obj['placement_xy_max']=hi;obj['placement_lot_m']=[hi[i]-lo[i] for i in range(2)]
        path=ROOT/'exports'/f'{key}.glb';G.export(coll,path);glb=G.glb_stats(path)
        assert glb['mesh_objects']==glb['primitives']==glb['materials']==1 and glb['textures']==0 and glb['all_primitives_have_vertex_color']
        report['models'][key]['glb']=glb
bpy.context.window.scene=bpy.data.scenes['EDIT • bookshop_level_3'];bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/integrated_models.blend'))
(ROOT/'reports/model_stats.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'reports/palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
print('NORMALIZATION_COMPLETE',T.protect(),flush=True)
