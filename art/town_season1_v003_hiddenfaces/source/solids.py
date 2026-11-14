"""Prove eligible occluders from the exact stage's editable, evaluated components."""
import bpy,bmesh,numpy as np,hashlib
from mathutils import Vector
from mathutils.kdtree import KDTree

def opaque(material):
    if not material or material.diffuse_color[3]<.999999 or not material.use_nodes:return False
    outputs=[n for n in material.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output]
    if len(outputs)!=1:return False
    output=outputs[0]
    if output.inputs['Volume'].is_linked or len(output.inputs['Surface'].links)!=1:return False
    node=output.inputs['Surface'].links[0].from_node
    if node.type!='BSDF_PRINCIPLED':return False
    for name,expected in [('Alpha',1.),('Transmission Weight',0.)]:
        socket=node.inputs.get(name)
        if socket is None or socket.is_linked or abs(socket.default_value-expected)>1e-7:return False
    return True

def collect(scene,glb_points):
    bpy.context.window.scene=scene;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    tree=KDTree(len(glb_points))
    for i,p in enumerate(glb_points):tree.insert(tuple(p),i)
    tree.balance();accepted=[];rejected={};parts=[]
    for obj in scene.objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
        try:
            vertices=np.array([tuple(ev.matrix_world@v.co) for v in me.vertices],dtype=np.float64)
            if len(vertices)<4:reason='fewer_than_four_vertices'
            elif not all(opaque(me.materials[p.material_index]) for p in me.polygons):reason='not_proven_opaque'
            elif ev.matrix_world.to_3x3().determinant()<=0:reason='non_positive_transform'
            else:reason=None
            if reason:
                rejected[reason]=rejected.get(reason,0)+1;continue
            bm=bmesh.new();bm.from_mesh(me);closed=all(e.is_manifold and e.is_contiguous for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
            normal_matrix=ev.matrix_world.to_3x3().inverted().transposed()
            normals=np.array([tuple((normal_matrix@p.normal).normalized()) for p in me.polygons],dtype=np.float64)
            offsets=np.array([float(Vector(n).dot(ev.matrix_world@p.center)) for n,p in zip(normals,me.polygons)],dtype=np.float64)
            if not closed:reason='open_or_inconsistent_component'
            elif volume<=1e-12:reason='not_positive_outward_volume'
            elif not np.isfinite(vertices).all() or not np.isfinite(normals).all():reason='non_finite'
            elif np.max(np.abs(np.linalg.norm(normals,axis=1)-1))>1e-5:reason='invalid_plane_normal'
            else:
                convex_error=float(np.max(vertices@normals.T-offsets))
                planar_error=max(float(np.max(np.abs(vertices[list(p.vertices)]@normals[i]-offsets[i]))) for i,p in enumerate(me.polygons))
                if convex_error>2e-5:reason='non_convex'
                elif planar_error>2e-6:reason='non_planar_face'
                else:
                    match_error=max(tree.find(tuple(p))[2] for p in vertices)
                    if match_error>2e-5:reason='not_matched_to_actual_glb'
            parts.append({'name':obj.name,'closed_consistently_oriented':closed,'signed_local_volume':volume,'eligible':reason is None})
            if reason:
                rejected[reason]=rejected.get(reason,0)+1;continue
            fingerprint=hashlib.sha256(vertices.tobytes()+normals.tobytes()+offsets.tobytes()).hexdigest()
            accepted.append({'name':obj.name,'lower':vertices.min(axis=0).tolist(),'upper':vertices.max(axis=0).tolist(),
                             'normals':normals.tolist(),'offsets':offsets.tolist(),'geometry_sha256':fingerprint,
                             'closed':True,'opaque':True,'outward_volume':volume,'convex_max_plane_error_m':convex_error,
                             'max_face_planarity_error_m':planar_error,'max_glb_vertex_match_error_m':match_error})
        finally:ev.to_mesh_clear()
    assert accepted,'No proven convex occluders'
    assert not rejected.get('not_matched_to_actual_glb'),('Source/GLB geometry mismatch',scene.name,rejected)
    return accepted,{'source_mesh_components':len([o for o in scene.objects if o.type=='MESH']),'eligible_occluders':len(accepted),'rejected_reasons':rejected,'components':parts}
