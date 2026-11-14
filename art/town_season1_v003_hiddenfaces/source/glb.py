"""Attribute-preserving static GLB access; no geometry is regenerated or rounded."""
from pathlib import Path
import json,struct,copy,hashlib
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
COMPONENT={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}
WIDTH={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def read(path):
    raw=Path(path).read_bytes();magic,version,total=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and total==len(raw)
    offset=12;chunks=[]
    while offset<len(raw):
        length,kind=struct.unpack_from('<II',raw,offset);chunks.append((kind,raw[offset+8:offset+8+length]));offset+=8+length
    assert len(chunks)==2 and chunks[0][0]==0x4e4f534a and chunks[1][0]==0x004e4942
    doc=json.loads(chunks[0][1]);assert len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0]
    return doc,chunks[1][1],raw

def accessor(doc,blob,index,raw=False):
    a=doc['accessors'][index];assert 'sparse' not in a
    v=doc['bufferViews'][a['bufferView']];assert v.get('buffer',0)==0
    fmt='<'+COMPONENT[a['componentType']]*WIDTH[a['type']];size=struct.calcsize(fmt);stride=v.get('byteStride',size);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    assert stride>=size and offset+(a['count']-1)*stride+size<=len(blob)
    if raw:return [blob[offset+i*stride:offset+i*stride+size] for i in range(a['count'])]
    return [struct.unpack_from(fmt,blob,offset+i*stride) for i in range(a['count'])]

def primitive(doc):
    assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
    p=doc['meshes'][0]['primitives'][0];assert p.get('mode',4)==4 and 'targets' not in p
    assert not doc.get('skins') and not doc.get('animations') and not doc.get('textures')
    assert len(doc['materials'])==1 and doc['materials'][0].get('alphaMode','OPAQUE')=='OPAQUE'
    assert all(k in p['attributes'] for k in ('POSITION','NORMAL','COLOR_0'))
    return p

def mesh_world(doc):
    from mathutils import Matrix,Quaternion,Vector
    parents={child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
    def matrix(index):
        n=doc['nodes'][index]
        if 'matrix' in n:local=Matrix([n['matrix'][i::4] for i in range(4)])
        else:
            q=n.get('rotation',[0,0,0,1]);local=Matrix.LocRotScale(Vector(n.get('translation',[0,0,0])),Quaternion((q[3],q[0],q[1],q[2])),Vector(n.get('scale',[1,1,1])))
        return matrix(parents[index])@local if index in parents else local
    ids=[i for i,n in enumerate(doc['nodes']) if n.get('mesh')==0];assert len(ids)==1
    return matrix(ids[0])

def blender_points(doc,positions):
    import numpy as np
    m=mesh_world(doc);p=np.asarray(positions,dtype=np.float64);world=p@np.array([list(row) for row in m.to_3x3()]).T+np.array(m.translation)
    result=world[:,[0,2,1]].copy();result[:,1]*=-1
    return result

def compact(doc,blob,kept_triangles,used):
    original=primitive(doc);out=copy.deepcopy(doc);out['bufferViews']=[];out['accessors']=[];data=bytearray();p=out['meshes'][0]['primitives'][0]
    mapping={old:new for new,old in enumerate(used)}
    def append(payload,definition,target):
        while len(data)%4:data.append(0)
        offset=len(data);data.extend(payload);view=len(out['bufferViews']);out['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(payload),'target':target})
        a={k:v for k,v in definition.items() if k not in ('bufferView','byteOffset','sparse')};a['bufferView']=view;out['accessors'].append(a);return len(out['accessors'])-1
    for semantic,index in original['attributes'].items():
        chunks=accessor(doc,blob,index,True);definition=copy.deepcopy(doc['accessors'][index]);definition['count']=len(used)
        if 'min' in definition or 'max' in definition:
            values=accessor(doc,blob,index);rows=[values[i] for i in used];definition['min']=[min(v[k] for v in rows) for k in range(len(rows[0]))];definition['max']=[max(v[k] for v in rows) for k in range(len(rows[0]))]
        p['attributes'][semantic]=append(b''.join(chunks[i] for i in used),definition,34962)
    flattened=[mapping[i] for tri in kept_triangles for i in tri];definition=copy.deepcopy(doc['accessors'][original['indices']]);definition['count']=len(flattened)
    assert definition['componentType'] in (5123,5125) and max(flattened)<(65536 if definition['componentType']==5123 else 2**32)
    if 'min' in definition:definition['min']=[min(flattened)]
    if 'max' in definition:definition['max']=[max(flattened)]
    p['indices']=append(struct.pack('<'+COMPONENT[definition['componentType']]*len(flattened),*flattened),definition,34963)
    while len(data)%4:data.append(0)
    out['buffers']=[{'byteLength':len(data)}];js=json.dumps(out,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    raw=struct.pack('<4sII',b'glTF',2,28+len(js)+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data
    return out,bytes(data),raw

def protect():
    protected=json.loads((ROOT/'reports/protected_inputs.json').read_text())
    assert all(sha(ART/p)==h for p,h in protected.items()),'Protected original/audit input changed'
    return len(protected)
