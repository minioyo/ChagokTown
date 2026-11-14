"""Make neutral paired QA plates and exact roof crops from completed fresh renders."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
from png_qa import load,png,metrics
manifest=json.loads((ROOT/'reports/manifest.json').read_text());groups={}
for path in sorted((ROOT/'reports').glob('renders_*.json')):
    record=json.loads(path.read_text());assert record['review_map_sha256']==F.sha(ROOT/'blend/roof_tones_review.blend')
    for row in record['records']:
        assert F.sha(ROOT/row['path'])==row['sha256']
        for key,h in row['asset_sha256'].items():
            entry=next(e for e in manifest['assets'] if f"{e['type']}_level_{e['level']}"==key)
            assert F.sha(F.ART/entry['source_path' if row['variant']=='before' else 'path'])==h
        assert row['variant'] not in groups.setdefault(row['case'],{}),('Duplicate render case',row['case'],row['variant'])
        groups[row['case']][row['variant']]=row
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;camera=bpy.data.objects.new('QA projection',bpy.data.cameras.new('QA projection'));scene.collection.objects.link(camera);scene.camera=camera
report={'pairs':{},'roof_crops':{},'intentional_change':'Bright roof tile RGB only. This is not pixel-equality testing of the v003 hidden-face optimization.',
        'plate_order':'Before v003 above; roof tones below; L1 L2 L3 left to right. Crops and overview: before left, after right.',
        'comparison_color':'Original normalized RGBA8 PNG code bytes, no view transform or gamma correction applied.'}
for case,variants in sorted(groups.items()):
    if set(variants)!={'before','after'}:continue
    before=variants['before'];after=variants['after'];assert before['presentation_sha256']==after['presentation_sha256'] and before['placements']==after['placements']
    a=load(before['path']);b=load(after['path']);assert a.shape==b.shape
    separator=np.ones((24,a.shape[1],4),dtype=np.float32);separator[:,:,:3]=.08;path=f'renders/comparisons/{case}_compare.png';png(ROOT/path,np.concatenate([b,separator,a],axis=0))
    row={'before':before['path'],'after':after['path'],'before_sha256':before['sha256'],'after_sha256':after['sha256'],'comparison':path,'comparison_sha256':F.sha(ROOT/path),
         'identical_camera_lighting_resolution_and_placements':True,'intentional_color_difference':metrics(a,b)}
    if not case.startswith('whole_'):
        kind=case.removesuffix('_roofs');entry=next(e for e in manifest['assets'] if e['type']==kind and e['level']==3);doc,blob,_=F.read(F.ART/entry['path']);p=F.primitive(doc);points=F.blender_points(doc,F.accessor(doc,blob,p['attributes']['POSITION']))
        presentation=before['presentation'];camera.matrix_world=Matrix(presentation['camera']['matrix']);camera.data.type='ORTHO';camera.data.ortho_scale=presentation['camera']['ortho_scale'];scene.render.resolution_x=presentation['resolution'][0];scene.render.resolution_y=presentation['resolution'][1];scene.render.resolution_percentage=100;bpy.context.view_layer.update()
        placement=next(r for r in before['placements'] if r['id']=='QA stage 3');transform=Matrix(placement['matrix']);uv=np.array([tuple(world_to_camera_view(scene,camera,transform@Vector(point)))[:2] for point in points]);h,w=a.shape[:2]
        lower=uv.min(axis=0);upper=uv.max(axis=0);lower[1]+=(upper[1]-lower[1])*.25;margin=.01
        x0=max(0,math.floor((lower[0]-margin)*w));x1=min(w,math.ceil((upper[0]+margin)*w));y0=max(0,math.floor((lower[1]-margin)*h));y1=min(h,math.ceil((upper[1]+margin)*h))
        aa=a[y0:y1,x0:x1];bb=b[y0:y1,x0:x1];bar=np.ones((len(aa),16,4),dtype=np.float32);bar[:,:,:3]=.08;detail=f'renders/comparisons/roof_detail_{kind}.png';png(ROOT/detail,np.concatenate([aa,bar,bb],axis=1))
        report['roof_crops'][kind]={'path':detail,'sha256':F.sha(ROOT/detail),'case':case,'stage':3,'same_source_pixel_roi_bottom_left':[x0,y0,x1,y1]}
    if case=='whole_final':
        # QA thumbnail: identical 4x4 box sampling of both PNGs, no color adjustment.
        def quarter(v):return v.reshape(v.shape[0]//4,4,v.shape[1]//4,4,4).mean(axis=(1,3))
        aa=quarter(a);bb=quarter(b);bar=np.ones((len(aa),16,4),dtype=np.float32);bar[:,:,:3]=.08;overview='renders/comparisons/whole_final_overview.png';png(ROOT/overview,np.concatenate([aa,bar,bb],axis=1));report['overview']={'path':overview,'sha256':F.sha(ROOT/overview),'sampling':'same 4x4 PNG-code box average, before left / after right'}
    report['pairs'][case]=row;print('ROOF_QA_PAIR',case,flush=True)
report['pair_count']=len(report['pairs']);report['all_required_pairs_present']=len(report['pairs'])==12 and len(report['roof_crops'])==8
report['source_render_records']={p.name:F.sha(p) for p in sorted((ROOT/'reports').glob('renders_*.json'))}
(ROOT/'reports/pixel_comparisons.json').write_text(json.dumps(report,indent=2),encoding='utf-8');F.protect();print('ROOF_QA_COMPLETE',len(report['pairs']),len(report['roof_crops']),flush=True)
