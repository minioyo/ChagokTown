"""Publish only the current validated GLBs, complete renders and manual visual reviews."""
from pathlib import Path
import ast,json,hashlib
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for p in (ROOT/'source').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read('reports/manifest.json');validation=read('reports/validation.json');changes=read('reports/roof_changes.json');pixels=read('reports/pixel_comparisons.json');review=read('source/reviewed_cases.json');protected=read('reports/protected_inputs.json')
assert len(manifest['assets'])==36 and manifest['changed_assets']==24 and manifest['unchanged_assets']==12 and len(list((ROOT/'exports').glob('*.glb')))==24
assert validation['passed'] and validation['manifest_sha256']==sha(ROOT/'reports/manifest.json') and validation['review_map_sha256']==sha(ROOT/'blend/roof_tones_review.blend')
assert pixels['all_required_pairs_present'] and set(review['cases'])==set(pixels['pairs']) and set(review['roof_crops'])==set(pixels['roof_crops']) and review['overview']
visual={'date':'2026-11-11','intentional_roof_color_change':True,'method':'Agent opened the actual paired renders, crops and overview. Geometry preservation was independently checked at raw byte level.','cases':{},'roof_crops':{}}
for case,row in pixels['pairs'].items():
    assert sha(ROOT/row['before'])==row['before_sha256'] and sha(ROOT/row['after'])==row['after_sha256'] and sha(ROOT/row['comparison'])==row['comparison_sha256']
    visual['cases'][case]={'note':review['cases'][case],'before_sha256':row['before_sha256'],'after_sha256':row['after_sha256'],'comparison_sha256':row['comparison_sha256']}
for kind,row in pixels['roof_crops'].items():
    assert sha(ROOT/row['path'])==row['sha256'];visual['roof_crops'][kind]={'note':review['roof_crops'][kind],**row}
assert sha(ROOT/pixels['overview']['path'])==pixels['overview']['sha256'];visual['overview']={'note':review['overview'],**pixels['overview']}
for p,h in pixels['source_render_records'].items():assert sha(ROOT/'reports'/p)==h
for entry in manifest['assets']:assert sha(ART/entry['path'])==entry['sha256'] and sha(ART/entry['source_path'])==entry['source_sha256']
assert all(sha(ART/p)==h for p,h in protected.items())
(ROOT/'reports/visual_review.json').write_text(json.dumps(visual,indent=2,ensure_ascii=False),encoding='utf-8')
labels={'bakery':'빵집','bookshop':'서점','cafe':'카페','cathedral':'성당','farmstead':'농가','florist':'꽃집','grocer':'잡화점','house':'주택','inn':'여관','town_hall':'마을회관','watermill':'방앗간','workshop':'작업장'}
def display_hex(rgb):
    def code(v):return v*12.92 if v<=.0031308 else 1.055*v**(1/2.4)-.055
    return '#'+''.join(f'{max(0,min(255,round(code(v)*255))):02X}' for v in rgb)
palette={}
for model in changes['models'].values():
    for part in model['components']:palette[part['material'],part['base_material']]=part
table=['| 밝은 기와 역할 | 기본색 | 이전 밝은색 | 수정 밝은색 |','|---|---|---|---|']
for (name,base),p in sorted(palette.items()):table.append(f"| {name} | {display_hex(p['base_linear_rgb'])} ({base}) | {display_hex(p['old_linear_rgb'])} | {display_hex(p['new_linear_rgb'])} |")
palette_text=['# 지붕 기와 색 수정 기록','', '기본색은 유지한다. 새 밝은색 = 기본색 + 0.10 × (기존 밝은색 - 기본색), 선형 RGB 채널 기준. HEX는 표시용 sRGB 8bit 반올림이며 정확한 납품 float 값과 정점 번호는 roof_changes.json에 있다.','']+table
palette_text+=['','## 실제 부품 범위','', '| 유형 | 단계 | 기와 부품 수 | 수정된 exported vertices | triangles 유지 |','|---|---:|---:|---:|---:|']
for key,row in sorted(changes['models'].items()):
    kind,level=key.rsplit('_level_',1);count=sum(bool(p['vertex_ids']) for p in row['components']);palette_text.append(f"| {labels[kind]} | {level} | {count} | {row['changed_vertex_count']} | {row['triangles']:,} |")
palette_text+=['','같은 색을 쓴 벽·창·차양·소품, 기본색 기와, 처마·용마루·굴뚝·온실은 변경하지 않았다. 완전히 가려져 v003에서 이미 없어진 면을 복원하지 않았다. 밝은 패치가 없는 서점·카페·잡화점·작업장은 원본 v003 파일을 참조한다.']
(ROOT/'reports/PALETTE.md').write_text('\n'.join(palette_text)+'\n',encoding='utf-8')
gallery=['# 지붕 패치 대비 전후 비교','', '전체/단계 비교는 **위 v003 / 아래 수정본**, 단계 행은 **왼쪽부터 L1·L2·L3**다. 확대와 작은 전체 보기는 **왼쪽 v003 / 오른쪽 수정본**이다. 조명·색 관리·카메라·해상도는 전후 동일하다.','',
         '- [작은 화면에서 전체 비교](comparisons/whole_final_overview.png)','- [최종 수정 전체 원본 크기](whole/final_after.png)','', '| 유형 | 전 단계 지붕 | L3 지붕 확대 |','|---|---|---|']
for kind in sorted(pixels['roof_crops']):gallery.append(f'| {labels[kind]} | [L1~L3](comparisons/{kind}_roofs_compare.png) | [확대](comparisons/roof_detail_{kind}.png) |')
gallery+=['','## 전체 성장 장면','']+[f'- [{case}](comparisons/{case}_compare.png)' for case in ('whole_beginning','whole_middle','whole_final','whole_final_top')]
(ROOT/'renders/GALLERY.md').write_text('\n'.join(gallery)+'\n',encoding='utf-8')
summary={'date':'2026-11-11','types_changed':8,'changed_glbs':manifest['changed_assets'],'unchanged_glbs_referenced':manifest['unchanged_assets'],'total_manifest_assets':len(manifest['assets']),
    'roof_patch_vertices_changed':sum(r['changed_vertex_count'] for r in changes['models'].values()),'triangles':sum(r['triangles'] for r in changes['models'].values()),'exported_vertices':sum(r['vertices'] for r in changes['models'].values()),
    'remaining_patch_contrast_linear_rgb':.10,'all_non_roof_rgb_bytes_identical':True,'hiddenface_topology_preserved':True,'protected_files_unchanged':len(protected),'paired_renders_reviewed':len(pixels['pairs']),'roof_crops_reviewed':len(pixels['roof_crops']),
    'manifest_sha256':sha(ROOT/'reports/manifest.json'),'review_map_sha256':sha(ROOT/'blend/roof_tones_review.blend'),'runtime_tested':False}
(ROOT/'reports/delivery.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
text='''# 차곡마을 · 지붕 패치 대비 정리 v004

2026-11-11. 사용자가 밝은 낱장 기와 때문에 낡고 덧댄 듯한 인상을 지적해, v003 내부 면 제거본 위에서 **밝은 기와의 COLOR_0 RGB만** 기본 지붕색에 가깝게 조정했다. 건물별 청록·살구·올리브·갈색·보라 계열과 기와 형상·분할은 유지했다.

- **수정 GLB 24개 / v003 그대로 참조 12개 / 전체 36개 연결.** [manifest](reports/manifest.json)의 `path`가 최종 파일이다. `source_path`는 v003 비교 입력이다. 미수정 12개를 새 파일인 것처럼 복제하지 않았다.
- [전체 수정 렌더](renders/whole/final_after.png), [작은 화면 전후 비교](renders/comparisons/whole_final_overview.png), [모든 단계·지붕 확대 갤러리](renders/GALLERY.md)
- [별도 검수 맵](blend/roof_tones_review.blend): `BEFORE v003 • beginning/middle/final`, `AFTER roof tones • beginning/middle/final`, 두 버전의 36개 자산 라이브러리. `ARCHIVE v002`는 이전 검수 맵에 있던 참고 장면이다.
- [색·부품 기록](reports/PALETTE.md), [정확한 부품별 float RGB·정점 번호](reports/roof_changes.json), [독립 검증](reports/validation.json), [시각 검수](reports/visual_review.json)

## 색과 수정 범위

기본색과 밝은 칸의 차이를 선형 RGB에서 기존의 **10%**만 남겼다. 화면 명도 대비를 수치로 90% 줄였다는 뜻은 아니다. 사각형 패치가 먼저 튀지 않되 입체 기와의 선은 남기는 강도다.

'''+ '\n'.join(table)+'''

수정 유형은 성당·여관·농가·방앗간·빵집·꽃집·주택·회관이다. 패치가 없는 서점·카페·잡화점·작업장은 유지했다. HEX는 표시용 반올림이며 실제 파일은 float RGB를 저장한다.

원본의 실제 단계 편집 장면에서 `Roof • tile panel`, `Roof • broad tile`, `Roof • broad tile colour` 부품을 식별했다. 평가된 부품의 위치와 재질색을 실제 v003 GLB 정점에 대응하고, 수정 정점이 다른 부품과 공유되지 않으며 해당 삼각형도 같은 기와 부품에 속하는지 검사했다. 색 값 전체 치환을 하지 않았다.

새 RGB 외에는 **GLB의 모든 바이트가 v003과 동일**하다. POSITION·NORMAL·인덱스·정점 수·삼각형 수·루트·축·스케일·재질·primitive·텍스처 수·파일 길이를 유지했다. 벽·문·창·처마·용마루·소품 색을 바꾸지 않았으며 숨은 면을 되살리거나 bevel/Decimate를 적용하지 않았다. 편집 원본은 그대로 보존했고 `editable_blend`/`editable_scene`과 색 오버레이 소스로 변경을 재현한다.

## 검증과 판단

- 36개 전후 자산의 색 범위를 원본 편집 부품에서 독립적으로 다시 계산하고, 허용한 기와 RGB 바이트 이외의 차이가 없음을 확인했다. 고유 36개 합계는 **115,877 triangles / 157,565 exported vertices**로 v003과 같다.
- 최종 납품 파일 36개와 비교 입력 36개를 새로 가져와 저장된 검수 맵의 실제 자산 데이터와 일치하는지 검사했다. 불투명 메시 1개·재질 1개·primitive 1개·텍스처 0개, 유한 단위 노멀·퇴화 삼각형 0개를 유지했다.
- 시작·중간·최종 장면의 지형·길·강·나무·공용 소품 메시·정점색·재질·배치, 카메라·조명·노출·색 관리 지문이 v003과 같다. 형상이 동일하므로 v003의 외곽·접근로 검증을 승계하며 이를 이번 새 엔진 이동 검사로 표현하지 않는다.
- v001/v002/v003·감사·고정 샘플 등 보호 입력 '''+str(len(protected))+'''개 SHA-256이 그대로다. 이 새 폴더 안에서만 파일을 만들었다.
- 실제 GLB를 다시 가져온 **전후 12쌍**을 새로 렌더했다. 시작·중간·최종 전체·최종 평면 4쌍과 수정 8종의 L1~L3 지붕 행 8쌍이다. 전체 2400×1500, 단계 행 3000×1600, Cycles 64 samples·seed 71로 전후 동일하다. 기존 PNG 존재로 렌더를 생략하지 않았다.
- 비교판 12개, 같은 픽셀 영역의 L3 지붕 확대 8개, 600px 크기의 작은 전체 비교를 직접 열어 확인했다. 큰 밝은 패치가 거의 튀지 않고 기와 선·두께·실루엣은 유지되는 것으로 판단했다. 이는 이번 승인된 지붕색 수정의 시각 판단이며 v003 내부 면 제거의 외관 불변 검사와 구분한다.

비교판·크롭은 원본 PNG 코드값을 재배열하며 색 보정하지 않는다. 작은 전체 보기는 양쪽에 동일한 4×4 박스 축소를 적용했다. 의도한 지붕색 변화와 간접광·샘플링 차이가 있으므로 픽셀 동일을 주장하지 않는다. Android 앱·고정 runtime_samples 교체나 Pleos·실차 성능 검증은 수행하지 않았다.

## 재현

기존 생성 드라이버를 실행하지 않는다. 프로젝트 루트에서 새 폴더의 소스만 실행한다.

```text
python -B art/town_season1_v004_roof_tones/source/prepare.py
python -B art/town_season1_v004_roof_tones/source/run.py tones
python -B art/town_season1_v004_roof_tones/source/run.py map
python -B art/town_season1_v004_roof_tones/source/run.py verify
python -B art/town_season1_v004_roof_tones/source/run.py render --batch preview
python -B art/town_season1_v004_roof_tones/source/run.py render --batch roofs_a
python -B art/town_season1_v004_roof_tones/source/run.py render --batch roofs_b
python -B art/town_season1_v004_roof_tones/source/run.py render --batch whole
python -B art/town_season1_v004_roof_tones/source/run.py pixels
```

이미지를 직접 검수하고 `source/reviewed_cases.json`을 갱신한 뒤 `python -B art/town_season1_v004_roof_tones/source/deliver.py`를 실행한다. 검수 맵·GLB·렌더 해시가 현재 결과와 일치해야 안내 파일을 생성한다.
'''
(ROOT/'README.md').write_text(text,encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
