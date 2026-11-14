"""Exact fingerprints for the unchanged environment, presentation and plot placement."""
import bpy,json,hashlib,numpy as np

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def value(v):
    if isinstance(v,(bool,int,float,str)) or v is None:return v
    try:return [value(x) for x in v]
    except TypeError:return getattr(v,'name',str(type(v)))

def nodes(tree):
    if tree is None:return None
    return {'nodes':sorted([{'name':n.name,'type':n.bl_idname,'inputs':[(s.name,value(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],
                            'outputs':[(s.name,value(s.default_value)) for s in n.outputs if hasattr(s,'default_value')],
                            'layer_name':getattr(n,'layer_name',None),'attribute_name':getattr(n,'attribute_name',None)} for n in tree.nodes],key=lambda n:n['name']),
            'links':sorted((l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links)}

def material(m):
    return {'name':m.name,'diffuse':list(m.diffuse_color),'backface_culling':m.use_backface_culling,'nodes':nodes(m.node_tree),'surface_render_method':getattr(m,'surface_render_method',None)}

def mesh_digest(obj,dg):
    ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();h=hashlib.sha256()
    h.update(np.array([v.co[:] for v in me.vertices],dtype='<f8').tobytes());h.update(np.array([t.vertices[:] for t in me.loop_triangles],dtype='<i8').tobytes())
    h.update(np.array([n.vector[:] for n in me.corner_normals],dtype='<f8').tobytes())
    h.update(json.dumps([(list(p.vertices),p.material_index,p.use_smooth) for p in me.polygons]).encode())
    for attr in me.color_attributes:
        h.update((attr.name+attr.domain+attr.data_type).encode());h.update(np.array([c.color[:] for c in attr.data],dtype='<f8').tobytes())
    materials=[material(m) if m else None for m in me.materials];ev.to_mesh_clear()
    return {'geometry_sha256':h.hexdigest(),'materials':materials}

def presentation(scene):
    camera=scene.camera
    return {'world':nodes(scene.world.node_tree) if scene.world else None,
      'camera':{'matrix':[list(r) for r in camera.matrix_world],'type':camera.data.type,'ortho_scale':camera.data.ortho_scale,'lens':camera.data.lens,
                'clip':[camera.data.clip_start,camera.data.clip_end],'dof':camera.data.dof.use_dof},
      'lights':sorted([{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),
                       'size':getattr(o.data,'size',None),'angle':getattr(o.data,'angle',None)} for o in scene.objects if o.type=='LIGHT'],key=lambda o:o['name']),
      'view':{k:getattr(scene.view_settings,k) for k in ('view_transform','look','exposure','gamma')},
      'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],
      'units':[scene.unit_settings.system,scene.unit_settings.scale_length]}

def snapshot(scene):
    bpy.context.window.scene=scene;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();objects={}
    for obj in scene.objects:
        if obj.get('plot_id'):continue
        row={'type':obj.type,'matrix':[list(r) for r in obj.matrix_world],'hide_render':obj.hide_render,'visible_camera':obj.visible_camera,'visible_shadow':obj.visible_shadow}
        if obj.type=='MESH':row.update(mesh_digest(obj,dg))
        objects[obj.name]=row
    return {'environment':objects,'environment_sha256':digest(objects),'presentation':presentation(scene),'presentation_sha256':digest(presentation(scene)),
            'plots':{o['plot_id']:{'kind':o['kind'],'level':o['level'],'matrix':[list(r) for r in o.matrix_world]} for o in scene.objects if o.get('plot_id')}}

def import_asset(path,scene,name):
    bpy.context.window.scene=scene;previous=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
    collection=bpy.data.collections.new(name);scene.collection.children.link(collection)
    for obj in set(scene.objects)-previous:
        for c in list(obj.users_collection):c.objects.unlink(obj)
        collection.objects.link(obj)
    assert len([o for o in collection.all_objects if o.type=='MESH'])==1
    return collection

def runtime_digest(collection):
    h=hashlib.sha256()
    for obj in collection.all_objects:
        if obj.type!='MESH':continue
        me=obj.data;me.calc_loop_triangles()
        h.update(np.array([tuple(obj.matrix_world@v.co) for v in me.vertices],dtype='<f8').tobytes())
        h.update(np.array([tuple(t.vertices) for t in me.loop_triangles],dtype='<i8').tobytes())
        h.update(np.array([tuple(n.vector) for n in me.corner_normals],dtype='<f8').tobytes())
        for a in me.color_attributes:h.update(np.array([tuple(c.color) for c in a.data],dtype='<f8').tobytes())
    return h.hexdigest()
