"""Audit-only L3 copies: remove triangles strictly inside other convex opaque parts.

Source GLBs and blend files stay unchanged. Vertex attribute bytes are copied exactly.
"""
from pathlib import Path
import bpy, numpy as np, json, struct, hashlib, copy
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ART=OUT.parents[2]/'art'
manifest=json.loads((ART/'town_season1_v002_integrated/reports/manifest.json').read_text())
(OUT/'hidden_face_candidates').mkdir(exist_ok=True)
report={'method':'Every removed triangle has all three vertices strictly inside a verified convex source component; 0.05mm margin.',
        'scope':'Audit-only L3 variants; not adopted runtime assets.', 'models':{}}

def access(j,data,index,raw=False):
    a=j['accessors'][index];v=j['bufferViews'][a['bufferView']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    fmt='<'+{5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]*width
    size=struct.calcsize(fmt);stride=v.get('byteStride',size);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    if raw:return [data[offset+i*stride:offset+i*stride+size] for i in range(a['count'])]
    return [struct.unpack_from(fmt,data,offset+i*stride) for i in range(a['count'])]

loaded=None
for entry in manifest['assets']:
    if entry['level']!=3:continue
    blend=ART/entry['editable_blend']
    if loaded!=blend:
        bpy.ops.wm.open_mainfile(filepath=str(blend));loaded=blend
    s=bpy.data.scenes[entry['editable_scene']];bpy.context.window.scene=s;bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get();occluders=[]
    for o in s.objects:
        if o.type!='MESH' or o.name.lower().startswith(('studio','backdrop','floor')):continue
        e=o.evaluated_get(dg);me=e.to_mesh()
        verts=np.array([tuple(e.matrix_world@v.co) for v in me.vertices],dtype=np.float64)
        if len(verts)<4:e.to_mesh_clear();continue
        nm=e.matrix_world.to_3x3().inverted().transposed()
        normals=[];offsets=[]
        for p in me.polygons:
            normal=(nm@p.normal).normalized();center=e.matrix_world@p.center
            normals.append(tuple(normal));offsets.append(normal.dot(center))
        e.to_mesh_clear();normals=np.array(normals);offsets=np.array(offsets)
        if len(normals)==0:continue
        # Convexity proof: all source vertices are behind every outward face plane.
        if np.max(verts@normals.T-offsets)>2e-5:continue
        occluders.append((verts.min(axis=0),verts.max(axis=0),normals,offsets,o.name))
    path=ART/entry['path'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256']
    n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);binary=raw[28+n:]
    assert len(j['meshes'])==1 and len(j['meshes'][0]['primitives'])==1
    p=j['meshes'][0]['primitives'][0]
    positions=np.array(access(j,binary,p['attributes']['POSITION']),dtype=np.float64)
    # The export's vertex positions already carry Blender->glTF basis conversion.
    points=positions[:,[0,2,1]].copy();points[:,1]*=-1
    indices=np.array(access(j,binary,p['indices']),dtype=np.int64).reshape(-1,3)
    triangles=points[indices];lo=triangles.min(axis=1);hi=triangles.max(axis=1)
    remove=np.zeros(len(indices),dtype=bool);by_occluder={};epsilon=5e-5
    for lower,upper,normals,offsets,name in occluders:
        eligible=np.where((~remove)&np.all(lo>=lower+epsilon,axis=1)&np.all(hi<=upper-epsilon,axis=1))[0]
        removed_here=0
        for start in range(0,len(eligible),512):
            batch=eligible[start:start+512]
            inside=np.all(triangles[batch]@normals.T < offsets-epsilon,axis=(1,2))
            remove[batch[inside]]=True;removed_here+=int(inside.sum())
        if removed_here:by_occluder[name]=removed_here
    kept=indices[~remove].reshape(-1).tolist();used=sorted(set(kept));mapping={old:new for new,old in enumerate(used)}
    doc=copy.deepcopy(j);doc['bufferViews']=[];doc['accessors']=[];blob=bytearray()
    def append_accessor(payload,definition):
        while len(blob)%4:blob.append(0)
        offset=len(blob);blob.extend(payload)
        view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(payload)})
        a={k:v for k,v in definition.items() if k not in ('bufferView','byteOffset','sparse')};a['bufferView']=view
        doc['accessors'].append(a);return len(doc['accessors'])-1
    outp=doc['meshes'][0]['primitives'][0]
    for semantic,index in p['attributes'].items():
        chunks=access(j,binary,index,True);definition=copy.deepcopy(j['accessors'][index]);definition['count']=len(used)
        if semantic=='POSITION':
            definition['min']=positions[used].min(axis=0).tolist();definition['max']=positions[used].max(axis=0).tolist()
        outp['attributes'][semantic]=append_accessor(b''.join(chunks[i] for i in used),definition)
    new_indices=[mapping[i] for i in kept]
    outp['indices']=append_accessor(struct.pack('<'+'H'*len(new_indices),*new_indices),
                                    {'componentType':5123,'count':len(new_indices),'type':'SCALAR'})
    while len(blob)%4:blob.append(0)
    doc['buffers']=[{'byteLength':len(blob)}]
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    output=struct.pack('<4sII',b'glTF',2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
    outpath=OUT/'hidden_face_candidates'/path.name;outpath.write_bytes(output)
    # Verify exact attribute values per retained index, including custom normals and vertex colors.
    for semantic,new_index in outp['attributes'].items():
        a=access(j,binary,p['attributes'][semantic],True);b=access(doc,blob,new_index,True)
        assert all(b[new]==a[old] for new,old in enumerate(used))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    report['models'][entry['type']]={'before_triangles':len(indices),'after_triangles':len(kept)//3,
                                     'before_vertices':len(points),'after_vertices':len(used),
                                     'removed_triangles':int(remove.sum()),'convex_occluders':len(occluders),
                                     'by_occluder':by_occluder,'attribute_bytes_preserved':True,
                                     'bytes_before':len(raw),'bytes_after':len(output),'source_sha256':entry['sha256']}
    print('CULLED',entry['type'],len(indices),len(kept)//3,len(points),len(used),flush=True)
totals={key:sum(report['models'][p['kind']][key] for p in manifest['layout']) for key in
        ('before_triangles','after_triangles','before_vertices','after_vertices','removed_triangles')}
report['fourteen_plot_totals']=totals
(OUT/'hidden_faces.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('HIDDEN_FACE_AUDIT_COMPLETE',totals,flush=True)
