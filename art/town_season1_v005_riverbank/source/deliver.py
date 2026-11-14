"""Verify final hashes and arrange unretouched paired renders for delivery."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT.parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
manifest=read(ROOT/'reports/manifest.json')
validation=read(ROOT/'reports/validation.json')
assert validation['passed']
blend=ROOT/'blend/riverbank_review.blend'
glb=ROOT/'exports/riverbank_props_v005.glb'
assert sha(blend)==validation['reopened_blend_sha256']==manifest['review_blend']['sha256']
assert sha(glb)==validation['delivered_glb_sha256']==manifest['riverbank']['sha256']
protected=read(ROOT/'reports/protected_inputs.json')
assert all(sha(ART/p)==h for p,h in protected.items())
records=[]
for batch in ('preview','whole','details'):
    data=read(ROOT/f'reports/renders_{batch}.json')
    assert data['review_blend_sha256']==sha(blend)
    for row in data['records']:
        assert sha(ROOT/row['path'])==row['sha256']
        if row['variant']=='after':assert row['props_sha256']==sha(glb)
    records.extend(data['records'])
assert len(records)==12
cases={r['case']:{v:next(t for t in records if t['case']==r['case'] and t['variant']==v) for v in ('before','after')} for r in records}
names={'whole_final':'Final town','whole_beginning':'Beginning town','whole_middle':'Middle town',
       'whole_final_top':'Top view','riverbank_upper':'Upper riverbank','riverbank_mill':'Watermill and downstream bank'}
folder=ROOT/'renders/comparisons';folder.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25)
small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
index=[]
for case,variants in cases.items():
    assert variants['before']['presentation_sha256']==variants['after']['presentation_sha256']
    sources=[Image.open(ROOT/variants[v]['path']).convert('RGB') for v in ('before','after')]
    assert sources[0].size==sources[1].size
    h=round(sources[0].height*1200/sources[0].width)
    panel=Image.new('RGB',(2400,h+52),(238,233,220));draw=ImageDraw.Draw(panel)
    for i,(v,im) in enumerate(zip(('before','after'),sources)):
        draw.text((i*1200+20,10),f'{names[case]}  |  {"BEFORE v004" if v=="before" else "AFTER v005"}',font=font,fill=(63,66,53))
        panel.paste(im.resize((1200,h),Image.Resampling.BOX),(i*1200,52))
    path=folder/f'{case}_comparison.png';panel.save(path)
    index.append({'case':case,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'source_render_sha256':{v:r['sha256'] for v,r in variants.items()}})

order=['whole_beginning','whole_middle','whole_final','whole_final_top','riverbank_upper','riverbank_mill']
sheet=Image.new('RGB',(1800,860),(238,233,220));draw=ImageDraw.Draw(sheet)
for i,case in enumerate(order):
    row=cases[case]['after'];im=Image.open(ROOT/row['path']).convert('RGB');im.thumbnail((600,392),Image.Resampling.BOX)
    x=(i%3)*600;y=(i//3)*430
    draw.text((x+12,y+6),names[case]+' - v005',font=small,fill=(63,66,53))
    sheet.paste(im,(x+(600-im.width)//2,y+34+(392-im.height)//2))
sheet.save(ROOT/'renders/review_contact_sheet.png')
delivery={'blend_sha256':sha(blend),'glb_sha256':sha(glb),'manifest_sha256':sha(ROOT/'reports/manifest.json'),
          'validation_sha256':sha(ROOT/'reports/validation.json'),'protected_inputs_rechecked':len(protected),
          'records':records,'comparisons':index,'comparison_processing':'Paired render RGB code values; identical BOX resize on each side and labels only. No color correction or painted scene details.',
          'contact_sheet_sha256':sha(ROOT/'renders/review_contact_sheet.png')}
review_path=ROOT/'reports/visual_review.json'
if review_path.exists():
    review=read(review_path)
    assert review['status']=='accepted_for_delivery'
    assert review['blend_sha256']==sha(blend) and review['glb_sha256']==sha(glb)
    for case in review['cases']:
        assert sha(ROOT/case['comparison_path'])==case['comparison_sha256']
        for variant in ('before','after'):
            assert case['source_render_sha256'][variant]==cases[case['case']][variant]['sha256']
    delivery['visual_review_sha256']=sha(review_path)
delivery['files']={p.relative_to(ROOT).as_posix():sha(p) for p in [ROOT/'README.md',ROOT/'reports/placements.json',ROOT/'reports/model_stats.json',ROOT/'reports/palette.json',*sorted((ROOT/'source').glob('*.py'))]}
(ROOT/'reports/delivery.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8')
print('DELIVERY_READY',len(records),'renders;',len(index),'paired comparisons;',len(protected),'protected inputs')
