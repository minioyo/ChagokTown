"""Identify exported vertices by exact-stage evaluated component geometry and color."""
import bpy,numpy as np
from mathutils.kdtree import KDTree
ROLES={'Roof • tile panel','Roof • broad tile','Roof • broad tile colour'}
BASE={'Clay light':'Clay','Teal light':'Teal','Butter':'Brass','Roof slate light':'Roof slate','Roof russet light':'Roof russet','Roof olive light':'Roof olive'}
REMAINING_CONTRAST=.10

def scope(scene,points,colors):
    bpy.context.window.scene=scene;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();parts=[];vertices=[];owners=[];source_colors=[]
    for obj in scene.objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh()
        try:
            for material_id in sorted({p.material_index for p in me.polygons}):
                material=me.materials[material_id];old=np.array(material.diffuse_color[:3],dtype=np.float64)
                role=obj.name.split('.')[0];base=BASE.get(material.name) if role in ROLES else None
                target=None
                if base:
                    assert bpy.data.materials.get(base)
                    base_rgb=np.array(bpy.data.materials[base].diffuse_color[:3],dtype=np.float64)
                    target=base_rgb+(old-base_rgb)*REMAINING_CONTRAST
                part={'name':obj.name,'role':role,'material':material.name,'old_linear_rgb':old.tolist(),'base_material':base,
                      'base_linear_rgb':base_rgb.tolist() if base else None,'new_linear_rgb':target.tolist() if base else None,'vertex_ids':[]}
                index=len(parts);parts.append(part)
                used={v for p in me.polygons if p.material_index==material_id for v in p.vertices}
                for vi in sorted(used):
                    vertices.append(tuple(ev.matrix_world@me.vertices[vi].co));owners.append(index);source_colors.append(old)
        finally:ev.to_mesh_clear()
    tree=KDTree(len(vertices))
    for i,p in enumerate(vertices):tree.insert(p,i)
    tree.balance();source_colors=np.array(source_colors);matches=[];changed={};max_error=0.
    for i,(point,color) in enumerate(zip(points,colors)):
        candidates=[(owners[j],distance) for _,j,distance in tree.find_range(tuple(point),2e-5) if np.max(np.abs(source_colors[j]-color[:3]))<2e-5]
        assert candidates,('Unmatched source vertex',scene.name,i,tuple(point),tuple(color))
        ids=sorted({j for j,d in candidates});matches.append(ids);max_error=max(max_error,min(d for j,d in candidates))
        targets=[parts[j] for j in ids if parts[j]['base_material']]
        if targets:
            assert len(targets)==len(ids),('A patch vertex is shared with an unchanged component',scene.name,i,ids)
            target=targets[0]['new_linear_rgb'];assert all(p['new_linear_rgb']==target for p in targets)
            changed[i]=target
            for j in ids:parts[j]['vertex_ids'].append(i)
    return {'parts':parts,'owners_per_vertex':matches,'changed':changed,'max_position_match_error_m':max_error}
