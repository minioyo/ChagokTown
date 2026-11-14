"""Quantify paired fresh renders and make color-faithful QA plates, never art edits."""
import bpy,sys,json,math,struct,zlib,binascii,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text());records=[]
for path in sorted((ROOT/'reports').glob('renders_*.json')):records.extend(json.loads(path.read_text())['records'])
groups={}
for r in records:
    assert F.sha(ROOT/r['path'])==r['sha256'],('Stale image',r['path'])
    for key,h in r['input_signature']['assets'].items():
        entry=next(e for e in manifest['assets'] if f"{e['type']}_level_{e['level']}"==key)
        assert F.sha(F.ART/(entry['path'] if r['variant']=='optimized' else entry['source_path']))==h,('Stale model in image',r['path'],key)
    groups.setdefault(r['case'],{})[r['variant']]=r

def load(relative):
    image=bpy.data.images.load(str(ROOT/relative),check_existing=False);w,h=image.size;values=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(values);bpy.data.images.remove(image)
    values=values.reshape(h,w,4)
    # Blender exposes these byte-image pixels as normalized display-code values.
    # Prove that interpretation against the first raw PNG pixel (all predictors zero).
    raw=(ROOT/relative).read_bytes();ww,hh,depth,color,_,_,interlace=struct.unpack_from('>IIBBBBB',raw,16)
    assert (ww,hh,depth,color,interlace)==(w,h,8,6,0)
    offset=8;idats=[]
    while offset<len(raw):
        length=struct.unpack_from('>I',raw,offset)[0];kind=raw[offset+4:offset+8]
        if kind==b'IDAT':idats.append(raw[offset+8:offset+8+length])
        offset+=12+length
    first=zlib.decompressobj().decompress(b''.join(idats),5)[1:5]
    assert bytes(np.rint(values[-1,0]*255).astype(np.uint8))==first
    assert np.max(np.abs(values*255-np.rint(values*255)))<1e-4
    return values

def png(path,codes):
    # Copy normalized PNG code bytes directly. No gamma/view/color adjustment.
    encoded=np.rint(np.clip(codes,0,1)*255).astype(np.uint8)
    encoded=np.flipud(encoded);h,w=encoded.shape[:2]
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',binascii.crc32(name+data)&0xffffffff)
    data=b''.join(b'\0'+row.tobytes() for row in encoded)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(data,6))+chunk(b'IEND',b''))

def metrics(a,b):
    diff=np.abs(a[:,:,:3]-b[:,:,:3]);maximum=diff.max(axis=2);where=np.argwhere(maximum>.01)
    def decode(rgb):return np.where(rgb<=.04045,rgb/12.92,np.power((rgb+.055)/1.055,2.4))
    linear=np.abs(decode(a[:,:,:3])-decode(b[:,:,:3]))
    return {'mean_png_code_rgb_abs_error':float(diff.mean()),'mean_display_linear_rgb_abs_error':float(linear.mean()),'png_code_rgb_rmse':float(np.sqrt(np.mean(diff*diff))),
            'max_png_code_channel_difference':float(diff.max()),'p99_max_channel_difference':float(np.quantile(maximum,.99)),
            'percent_pixels_over_0_01':float(np.mean(maximum>.01)*100),'percent_pixels_over_0_003':float(np.mean(maximum>.003)*100),
            'difference_over_0_01_bbox_bottom_left':([int(where[:,1].min()),int(where[:,0].min()),int(where[:,1].max()),int(where[:,0].max())] if len(where) else None)}

features={'cathedral_front': [('portal_rose_arch',(0,-3.65,3.2),3.15),('roof_corner',(1.8,-.5,6.1),2.15)],
          'cafe_front':[('upper_window_frames',(.79,-1.5,3.17),1.3),('hip_roof_corner',(1.55,-1.25,4.5),1.1)],
          'florist_side':[('greenhouse_corners',(1.85,.08,1.35),1.65)],
          'watermill_side':[('wheel_and_bearing',(2.58,.15,1.43),1.9)],
          'house_front':[('balcony_door_and_corners',(.65,-1.5,2.95),1.45)],
          'bookshop_back':[('lookout_roof',(.83,.25,6.2),1.6)],
          'grocer_back':[('loft_window',(-.94,1.22,3.31),1.1)]}
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;camera=bpy.data.objects.new('QA pixel projection',bpy.data.cameras.new('QA pixel projection'));scene.collection.objects.link(camera);scene.camera=camera
report={'pairs':{},'cropped_features':[],'comparison_plate_order':'Original above; optimized below. Every row is L1, L2, L3 from left to right.',
        'feature_plate_order':'Original left; optimized right. These are identical pixel crops, not a new render or color adjustment.',
        'pixel_interpretation':'RGBA8 PNG code bytes confirmed against raw first-pixel bytes and integer code grid. Linear metric uses inverse sRGB on the display-referred PNG, not inverse AgX or scene radiance.',
        'limits':'PNG differences are auxiliary; five changed-seed controls measure Cycles sampling variation. Pixel-perfect equality is not claimed.'}
for case,variants in sorted(groups.items()):
    if not {'original','optimized'}<=variants.keys():continue
    original=variants['original'];optimized=variants['optimized'];assert original['camera_lighting_color_signature']==optimized['camera_lighting_color_signature']
    assert original['input_signature']['placements']==optimized['input_signature']['placements']
    a=load(original['path']);b=load(optimized['path']);assert a.shape==b.shape
    row=metrics(a,b);row.update({'original_image_sha256':original['sha256'],'optimized_image_sha256':optimized['sha256'],'same_camera_lighting_color_resolution':True,
                               'original':original['path'],'optimized':optimized['path'],'comparison':f'renders/comparisons/{case}_compare.png','heatmap':f'renders/comparisons/{case}_difference_x20.png'})
    if 'noise_control' in variants:
        control=variants['noise_control'];assert control['camera_lighting_color_signature']==original['camera_lighting_color_signature'];noise=load(control['path']);row['different_seed_control']=metrics(a,noise)
        row['mae_fraction_of_sampling_control']=row['mean_png_code_rgb_abs_error']/max(row['different_seed_control']['mean_png_code_rgb_abs_error'],1e-12)
    separator=np.ones((24,a.shape[1],4),dtype=np.float32);separator[:,:,:3]=.08
    png(ROOT/row['comparison'],np.concatenate([b,separator,a],axis=0))
    difference=np.clip(np.abs(a-b)*20,0,1);difference[:,:,3]=1;png(ROOT/row['heatmap'],difference)
    if case in features:
        signature=original['input_signature'];p=signature['presentation'];camera.matrix_world=Matrix(p['camera']['matrix']);camera.data.type='ORTHO';camera.data.ortho_scale=p['camera']['ortho_scale']
        scene.render.resolution_x=p['resolution'][0];scene.render.resolution_y=p['resolution'][1];scene.render.resolution_percentage=100;bpy.context.view_layer.update()
        instance=next(r for r in signature['placements'] if r['id']=='QA stage 3');transform=Matrix(instance['matrix'])
        for name,centre,radius in features[case]:
            world=transform@Vector(centre);uv=world_to_camera_view(scene,camera,world);h,w=a.shape[:2];cx=uv.x*w;cy=uv.y*h;rr=radius*w/camera.data.ortho_scale
            x0=max(0,math.floor(cx-rr));x1=min(w,math.ceil(cx+rr));y0=max(0,math.floor(cy-rr));y1=min(h,math.ceil(cy+rr));assert x1>x0 and y1>y0
            aa=a[y0:y1,x0:x1];bb=b[y0:y1,x0:x1];bar=np.ones((len(aa),16,4),dtype=np.float32);bar[:,:,:3]=.08
            path=f'renders/comparisons/detail_{name}.png';png(ROOT/path,np.concatenate([aa,bar,bb],axis=1))
            report['cropped_features'].append({'case':case,'feature':name,'stage':3,'path':path,'source_pixel_roi_bottom_left':[x0,y0,x1,y1],'difference':metrics(aa,bb)})
    report['pairs'][case]=row;print('PIXEL_PAIR',case,row['mean_png_code_rgb_abs_error'],row['percent_pixels_over_0_01'],flush=True)
report['pair_count']=len(report['pairs']);report['model_direction_cases']=len([k for k in report['pairs'] if not k.startswith('whole_')]);report['sampling_controls']=sum('different_seed_control' in r for r in report['pairs'].values())
report['all_required_pairs_present']=report['pair_count']==40 and report['model_direction_cases']==36 and report['sampling_controls']==5
report['source_render_records']={p.name:F.sha(p) for p in sorted((ROOT/'reports').glob('renders_*.json'))}
(ROOT/'reports/pixel_metrics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PIXEL_COMPARISON_COMPLETE',report['pair_count'],report['model_direction_cases'],report['sampling_controls'],flush=True)
