"""Read-only inventory of every model referenced by the accepted integrated map."""
from pathlib import Path
import collections, hashlib, json, math, struct

OUT=Path(__file__).resolve().parent
PROJECT=OUT.parents[2]
ART=PROJECT/'art'
manifest=json.loads((ART/'town_season1_v002_integrated/reports/manifest.json').read_text())
models={}
for entry in manifest['assets']:
    path=ART/entry['path'];raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==entry['sha256'],path
    magic,version,size=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and size==len(raw)
    n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);binary=raw[28+n:]
    def values(index):
        a=j['accessors'][index];v=j['bufferViews'][a['bufferView']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        fmt='<'+{5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]*width
        stride=v.get('byteStride',struct.calcsize(fmt));offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        return [struct.unpack_from(fmt,binary,offset+i*stride) for i in range(a['count'])]
    vertices=triangles=duplicate_full_attributes=unique_positions=unused_vertices=0
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            assert p.get('mode',4)==4
            attrs={key:values(index) for key,index in sorted(p['attributes'].items())}
            assert 'COLOR_0' in attrs and 'NORMAL' in attrs
            count=len(attrs['POSITION']);vertices+=count
            indices=[x[0] for x in values(p['indices'])];triangles+=len(indices)//3
            assert len(indices)%3==0 and max(indices)<count
            unused_vertices+=count-len(set(indices))
            duplicate_full_attributes+=count-len(set(zip(*attrs.values())))
            unique_positions+=len(set(attrs['POSITION']))
            assert all(math.isfinite(x) for v in attrs['NORMAL'] for x in v)
            assert all(abs(sum(x*x for x in v)-1)<.002 for v in attrs['NORMAL'])
    key=f"{entry['type']}_level_{entry['level']}"
    models[key]={'kind':entry['type'],'level':entry['level'],'path':entry['path'],
                 'triangles':triangles,'exported_vertices':vertices,
                 'unique_positions':unique_positions,'exact_attribute_duplicates':duplicate_full_attributes,
                 'unused_vertices':unused_vertices,'bytes':len(raw),'sha256':entry['sha256'],
                 'meshes':len(j['meshes']),'materials':len(j['materials']),
                 'primitives':sum(len(m['primitives']) for m in j['meshes']),
                 'textures':len(j.get('textures',[]))}
by_kind=collections.defaultdict(list)
for item in models.values():by_kind[item['kind']].append(item['level'])
assert len(by_kind)==12 and all(sorted(levels)==[1,2,3] for levels in by_kind.values())
assert len(manifest['layout'])==14
totals={}
for level in (1,2,3):
    used=[models[f"{plot['kind']}_level_{level}"] for plot in manifest['layout']]
    totals[str(level)]={name:sum(m[name] for m in used) for name in ['triangles','exported_vertices','bytes','exact_attribute_duplicates']}
result={'types':12,'plots':14,'assets':len(models),'all_level_paths_and_hashes_passed':True,
        'models':models,'fourteen_plot_totals_by_level':totals,
        'all_files_bytes':sum(m['bytes'] for m in models.values()),
        'exact_attribute_duplicates_total':sum(m['exact_attribute_duplicates'] for m in models.values()),
        'unused_vertices_total':sum(m['unused_vertices'] for m in models.values())}
(OUT/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))
print('L3_BY_TYPE',json.dumps({k:{s:m[s] for s in ('triangles','exported_vertices','exact_attribute_duplicates')} for k,m in models.items() if m['level']==3}))
