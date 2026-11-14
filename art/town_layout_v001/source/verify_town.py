"""Independent GLB byte checks, maximum-lot collisions, blend reopen and reimport."""
import sys, math, json, struct, hashlib
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
layout=json.loads((ROOT/'source/layout.json').read_text(encoding='utf-8'))
assembly=json.loads((ROOT/'reports/assembly.json').read_text())
assert not assembly['preview'] and not assembly['missing_models']

def glb(path,building=False):
    raw=path.read_bytes();magic,version,total=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and total==len(raw)
    n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);data=raw[28+n:]
    assert not doc.get('textures') and not doc.get('images') and not doc.get('cameras')
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        fmt='<'+{5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]*{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',struct.calcsize(fmt))
        return [struct.unpack_from(fmt,data,offset+i*stride) for i in range(a['count'])]
    triangles=0;primitives=0;min_area=math.inf
    for m in doc['meshes']:
        for p in m['primitives']:
            primitives+=1;assert p.get('mode',4)==4 and 'COLOR_0' in p['attributes']
            positions=accessor(p['attributes']['POSITION']);normals=accessor(p['attributes']['NORMAL'])
            assert all(math.isfinite(v) for pos in positions+normals for v in pos)
            assert all(abs(sum(v*v for v in no)-1)<.002 for no in normals)
            indices=[x[0] for x in accessor(p['indices'])];assert len(indices)%3==0
            assert max(indices)<len(positions)
            for i in range(0,len(indices),3):
                a,b,c=(Vector(positions[j]) for j in indices[i:i+3]);area=(b-a).cross(c-a).length/2
                assert area>1e-12,(path.name,i,'degenerate triangle')
                min_area=min(min_area,area)
            triangles+=len(indices)//3
            if building:
                # glTF +Y up to Blender +Z up.
                points=[(x,-z,y) for x,y,z in positions]
                lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
                assert abs(lo[2])<1e-5 and lo[0]>=-2.40001 and lo[1]>=-3.20001 and hi[0]<=2.40001 and hi[1]<=1.60001
    for mat in doc['materials']:
        assert mat.get('alphaMode','OPAQUE')=='OPAQUE'
        if building:assert not mat.get('doubleSided',False)
    if building:
        assert len(doc['meshes'])==len(doc['materials'])==primitives==1
        level=int(path.stem[-1]);assert triangles<={1:4000,2:6000,3:8000}[level]
    return {'triangles':triangles,'meshes':len(doc['meshes']),'materials':len(doc['materials']),
            'primitives':primitives,'textures':0,'bytes':len(raw),'finite_unit_normals':True,
            'degenerate_triangles':0,'minimum_triangle_area':min_area,'sha256':hashlib.sha256(raw).hexdigest()}

models={}
for slot in layout['slots']:
    for level in (1,2,3):
        path=ART/slot['source']/'exports'/f"{slot['kind']}_level_{level}.glb"
        entry=glb(path,True)
        report=json.loads((ART/slot['source']/'reports/validation.json').read_text())
        assert report['all_passed'] and report['models'][path.stem]['sha256']==entry['sha256']
        models[path.stem]=entry
assert len(models)==24
for path,h in assembly['source_glbs_unchanged'].items():assert hashlib.sha256((ART/path).read_bytes()).hexdigest()==h

def corners(slot):
    x,y=slot['xy'];a=math.radians(slot['yaw_deg']);c,s=math.cos(a),math.sin(a)
    return [(x+c*xx-s*yy,y+s*xx+c*yy) for xx,yy in [(-2.4,-3.2),(2.4,-3.2),(2.4,1.6),(-2.4,1.6)]]
def overlaps(a,b):
    for poly in (a,b):
        for i in range(4):
            dx=poly[(i+1)%4][0]-poly[i][0];dy=poly[(i+1)%4][1]-poly[i][1]
            av=[-dy*x+dx*y for x,y in a];bv=[-dy*x+dx*y for x,y in b]
            if max(av)<=min(bv) or max(bv)<=min(av):return False
    return True
lots={s['id']:corners(s) for s in layout['slots']}
for i,a in enumerate(layout['slots']):
    assert all((x/18.45)**2+((y-.3)/12.85)**2<1 for x,y in lots[a['id']]),a['id']
    for b in layout['slots'][i+1:]:assert not overlaps(lots[a['id']],lots[b['id']]),(a['id'],b['id'])

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_fixed_town_v001.blend'))
assert not any(o.type=='FONT' for o in bpy.data.objects)
scene_reports={};camera=None
for stage,levels in layout['stages'].items():
    s=bpy.data.scenes[stage];bpy.context.window.scene=s;bpy.context.view_layer.update()
    current_camera=(tuple(s.camera.location),tuple(s.camera.rotation_euler),s.camera.data.ortho_scale)
    if camera is None:camera=current_camera
    assert current_camera==camera
    actual={o['slot_id']:o for o in s.objects if 'slot_id' in o}
    assert set(actual)==set(levels)
    boxes={}
    for slot in layout['slots']:
        if slot['id'] not in actual:continue
        o=actual[slot['id']];assert o['level']==levels[slot['id']]
        assert (o.location-Vector((*slot['xy'],0))).length<1e-5
        assert abs(o.rotation_euler.z-math.radians(slot['yaw_deg']))<1e-5
        pts=[world_to_camera_view(s,s.camera,o.matrix_world@Vector(p)) for p in o.bound_box]
        bounds=[min(p.x for p in pts),min(p.y for p in pts),max(p.x for p in pts),max(p.y for p in pts)]
        assert min(bounds)>=0 and max(bounds)<=1,(slot['id'],'camera crop')
        boxes[slot['id']]=bounds
    scene_reports[stage]={'fixed_slots':list(actual),'normalized_screen_bounds':boxes}

exports={}
for name in ('town_environment','town_early','town_growing','town_mature'):
    path=ROOT/'exports'/f'{name}.glb';exports[name]=glb(path)
    scene=bpy.data.scenes.new('VERIFY • '+name);bpy.context.window.scene=scene
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects=[o for o in scene.objects if o.type=='MESH'];tris=0
    for o in objects:
        o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
        assert all(t.area>1e-12 for t in o.data.loop_triangles)
        assert all(math.isfinite(c) for n in o.data.corner_normals for c in n.vector)
    assert tris==exports[name]['triangles']
    exports[name]['reimport_passed']=True

out={'all_passed':True,'blend_reopened':True,'models_checked':24,'models':models,
     'maximum_lots_do_not_overlap':True,'lots_inside_island':True,'stage_positions_unchanged':True,
     'overview_cameras_identical':True,'buildings_inside_camera':True,'scene_checks':scene_reports,'exports':exports,
     'limits':'Offline geometry and framing only. No Android/Pleos/vehicle performance or gameplay validation.'}
(ROOT/'reports/validation.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('TOWN_VALIDATION_PASSED',len(models),exports['town_mature']['triangles'],flush=True)
