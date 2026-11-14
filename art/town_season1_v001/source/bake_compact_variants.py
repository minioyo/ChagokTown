"""Bake the two existing Compact variants without editing any prior artifact."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import geometry as G
import scene_common as C
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/'town_layout_v003_density/blend/chagok_density_comparison.blend'))
compact=bpy.data.scenes['Compact • same eight models']
source={o['kind']:o.instance_collection for o in C.models_in(compact) if o['kind'] in ('bakery','bookshop')}
for scene in bpy.data.scenes:
    for layer in scene.view_layers:
        for obj in layer.objects:obj.select_set(False,view_layer=layer)
material=bpy.data.materials.new('Compact variant • preserved vertex colour');material.use_nodes=True;material.use_backface_culling=True
bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Metallic'].default_value=0;bsdf.inputs['Roughness'].default_value=.68
vc=material.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Palette';material.node_tree.links.new(vc.outputs['Color'],bsdf.inputs['Base Color'])
folder=ROOT/'exports/reused_compact';folder.mkdir(exist_ok=True);report={}
for kind,col in source.items():
    scene=bpy.data.scenes.new('BAKE • '+kind);bpy.context.window.scene=scene
    target=bpy.data.collections.new('BAKE • '+kind);scene.collection.children.link(target)
    scene.collection.children.link(col);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();source_stats=G.stats(col)
    for original in col.all_objects:
        if original.type!='MESH':continue
        ev=original.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg)
        active=me.color_attributes.active_color
        if active:
            colours=[tuple(active.data[loop.vertex_index if active.domain=='POINT' else i].color) for i,loop in enumerate(me.loops)]
        else:colours=[tuple(me.materials[poly.material_index].diffuse_color) for poly in me.polygons for _ in poly.loop_indices]
        for attr in list(me.color_attributes):me.color_attributes.remove(attr)
        attr=me.color_attributes.new(name='Palette',type='BYTE_COLOR',domain='CORNER')
        for entry,color in zip(attr.data,colours):entry.color=color
        for poly in me.polygons:poly.material_index=0
        me.materials.clear();me.materials.append(material);me.transform(original.matrix_world)
        obj=bpy.data.objects.new(kind+' • baked existing component',me);target.objects.link(obj);obj.matrix_world=Matrix.Identity(4);obj.select_set(True)
    scene.collection.children.unlink(col)
    bpy.context.view_layer.objects.active=next(o for o in target.objects if o.type=='MESH')
    if len(target.objects)>1:bpy.ops.object.join()
    obj=bpy.context.view_layer.objects.active
    obj.name=kind+'_level_3_compact_variant';tri=obj.modifiers.new('Explicit runtime triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
    path=folder/f'{kind}_level_3.glb';G.export(target,path);glb=G.glb_stats(path);baked_stats=G.stats(target)
    assert glb['mesh_objects']==glb['materials']==glb['primitives']==1
    assert glb['textures']==0 and glb['all_primitives_have_vertex_color']
    assert source_stats['triangles']==baked_stats['triangles']
    assert max(abs(a-b) for a,b in zip(source_stats['bounds_min']+source_stats['bounds_max'],baked_stats['bounds_min']+baked_stats['bounds_max']))<1e-5
    report[kind]={'source':source_stats,'baked':baked_stats,'glb':glb,'appearance_geometry_preserved':True}
(ROOT/'reports/reused_compact_variants.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
C.protect();print('COMPACT_VARIANTS_BAKED',flush=True)
