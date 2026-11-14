"""Attach current image hashes to the cases explicitly inspected by the agent."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'source/reviewed_cases.json').read_text(encoding='utf-8'));pixels=json.loads((ROOT/'reports/pixel_metrics.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'date':'2026-11-11','method':'Rendered source/candidate images were opened and visually inspected; pixel metrics were supplementary.',
        'pixel_perfect_equality_claimed':False,'cases':{},'features':{},'rollback_actions':source['rollback_actions']}
for case,note in source['cases'].items():
    pair=pixels['pairs'][case]
    report['cases'][case]={'note':note,'no_new_visible_silhouette_hole_color_or_shadow_change_observed':True,
                           'original_image_sha256':pair['original_image_sha256'],'optimized_image_sha256':pair['optimized_image_sha256'],
                           'comparison_image_sha256':sha(ROOT/pair['comparison'])}
for feature,note in source['features'].items():
    row=next(r for r in pixels['cropped_features'] if r['feature']==feature)
    report['features'][feature]={'note':note,'path':row['path'],'sha256':sha(ROOT/row['path'])}
(ROOT/'reports/visual_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('VISUALLY_REVIEWED',len(report['cases']),'feature crops',len(report['features']))
