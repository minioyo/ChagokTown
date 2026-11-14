"""Publish the index only after current-asset verification and visual review are complete."""
from pathlib import Path
import ast,json,hashlib
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for path in (ROOT/'source').glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read('reports/manifest.json');stats=read('reports/optimization.json');validation=read('reports/validation.json');pixels=read('reports/pixel_metrics.json');visual=read('reports/visual_review.json')
assert len(manifest['assets'])==36 and len(list((ROOT/'exports').glob('*.glb')))==36
assert validation['passed'] and validation['review_blend_sha256']==sha(ROOT/'blend/hiddenfaces_review.blend') and validation['manifest_sha256']==sha(ROOT/'reports/manifest.json')
assert pixels['all_required_pairs_present'] and set(visual['cases'])==set(pixels['pairs']) and len(visual['features'])==9
for case,row in pixels['pairs'].items():
    review=visual['cases'][case]
    assert review['original_image_sha256']==row['original_image_sha256']==sha(ROOT/row['original'])
    assert review['optimized_image_sha256']==row['optimized_image_sha256']==sha(ROOT/row['optimized'])
    assert review['comparison_image_sha256']==sha(ROOT/row['comparison'])
for row in visual['features'].values():assert row['sha256']==sha(ROOT/row['path'])
for p,h in pixels['source_render_records'].items():assert sha(ROOT/'reports'/p)==h
for a in manifest['assets']:assert sha(ART/a['path'])==a['sha256'] and sha(ART/a['source_path'])==a['source_sha256']
protected=read('reports/protected_inputs.json');assert all(sha(ART/p)==h for p,h in protected.items())
fields=('triangles_before','triangles_after','vertices_before','vertices_after','bytes_before','bytes_after')
unique={f:sum(r[f] for r in stats['models'].values()) for f in fields}
baseline=read('reports/environment_baseline.json');active={}
for label,row in baseline.items():
    active[label]={f:sum(stats['models'][f"{p['kind']}_level_{p['level']}"][f] for p in row['plots'].values()) for f in fields}
    active[label]['plots']=len(row['plots'])
labels={'bakery':'빵집','bookshop':'서점','cafe':'카페','cathedral':'성당','farmstead':'농가','florist':'꽃집','grocer':'잡화점','house':'주택','inn':'여관','town_hall':'마을회관','watermill':'방앗간','workshop':'작업장'}
fmt=lambda n:f'{n:,}'
percent=lambda before,after:100*(before-after)/before
stage_table=['| 14필지를 모두 해당 단계로 놓을 때 | triangles 전 → 후 | 실제 exported vertices 전 → 후 | GLB bytes 전 → 후 |','|---|---:|---:|---:|']
for n,row in stats['all_fourteen_plots_by_stage'].items():stage_table.append(f"| L{n} | {fmt(row['triangles_before'])} → {fmt(row['triangles_after'])} (-{percent(row['triangles_before'],row['triangles_after']):.1f}%) | {fmt(row['vertices_before'])} → {fmt(row['vertices_after'])} | {fmt(row['bytes_before'])} → {fmt(row['bytes_after'])} |")
detail=['# 전 단계 내부 면 제거 실측','', '정점은 GLB POSITION accessor의 실제 count다. Blender가 가져오며 용접한 정점 수를 대신 쓰지 않았다.', '',
        '| 유형 | 단계 | triangles 전 → 후 | 감소 | exported vertices 전 → 후 | GLB bytes 전 → 후 |','|---|---:|---:|---:|---:|---:|']
for key,row in sorted(stats['models'].items()):detail.append(f"| {labels[row['type']]} | {row['level']} | {fmt(row['triangles_before'])} → {fmt(row['triangles_after'])} | {percent(row['triangles_before'],row['triangles_after']):.1f}% | {fmt(row['vertices_before'])} → {fmt(row['vertices_after'])} | {fmt(row['bytes_before'])} → {fmt(row['bytes_after'])} |")
detail+=['','## 고유한 36개 파일 합계','',f"- triangles: {fmt(unique['triangles_before'])} → {fmt(unique['triangles_after'])}",f"- exported vertices: {fmt(unique['vertices_before'])} → {fmt(unique['vertices_after'])}",f"- bytes: {fmt(unique['bytes_before'])} → {fmt(unique['bytes_after'])}",'','## 14필지 가중 합계','']+stage_table
detail+=['','주택은 세 곳에 재사용되므로 14필지 합계에는 같은 주택 파일이 세 번 들어간다. 이는 실제 GPU 메모리·드로 호출·다운로드 용량을 뜻하지 않는다.','',
         '## 실제 성장 장면의 건물만 합계','', '| 장면 | 채수 | triangles 전 → 후 | exported vertices 전 → 후 | bytes 가중 합계 전 → 후 |','|---|---:|---:|---:|---:|']
for label in ('beginning','middle','final'):
    r=active[label];detail.append(f"| {label} | {r['plots']} | {fmt(r['triangles_before'])} → {fmt(r['triangles_after'])} | {fmt(r['vertices_before'])} → {fmt(r['vertices_after'])} | {fmt(r['bytes_before'])} → {fmt(r['bytes_after'])} |")
(ROOT/'reports/STATS.md').write_text('\n'.join(detail)+'\n',encoding='utf-8')
gallery=['# 원본·내부 면 제거 외관 비교','', '비교판은 **윗줄 원본 / 아랫줄 최적화**, 각 줄 **왼쪽부터 L1·L2·L3**다. 원래 렌더 PNG 코드 바이트를 재배열했으며 색 보정하지 않았다. 세부 크롭은 **왼쪽 원본 / 오른쪽 최적화**다.','',
         '| 유형 | 정면 | 후면 | 측면 |','|---|---|---|---|']
for kind,label in labels.items():gallery.append(f'| {label} | [정면](comparisons/{kind}_front_compare.png) | [후면](comparisons/{kind}_back_compare.png) | [측면](comparisons/{kind}_side_compare.png) |')
gallery+=['','## 전체 성장 장면','']+[f'- [{label} 전후](comparisons/whole_{label}_compare.png)' for label in ('beginning','middle','final','final_top')]
gallery+=['','## 같은 픽셀 영역 확대','']+[f"- [{row['feature']}](comparisons/detail_{row['feature']}.png)" for row in pixels['cropped_features']]
(ROOT/'renders/GALLERY.md').write_text('\n'.join(gallery)+'\n',encoding='utf-8')
summary={'date':'2026-11-11','scope':'All 12 types and levels 1–3; hidden triangles only; original design and all terrain/environment preserved.',
         'files':36,'types':12,'levels':[1,2,3],'unique_asset_totals':unique,'fourteen_plot_totals_by_stage':stats['all_fourteen_plots_by_stage'],'active_building_scene_totals':active,
         'independent_reimports':36,'maximum_stage_hulls_unchanged':True,'primary_entry_stage_cases':42,'render_pairs_visually_reviewed':40,'detail_crops_reviewed':9,'sampling_controls':5,
         'protected_original_files_unchanged':len(protected),'review_map_sha256':sha(ROOT/'blend/hiddenfaces_review.blend'),'runtime_performance_measured':False}
(ROOT/'reports/delivery.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
final=pixels['pairs']['whole_final'];noise=final['different_seed_control']
text='''# 차곡마을 시즌 1 · 전 단계 내부 면 제거 v003

2026-11-11. 통합 v002의 디자인·구도·비례와 지형을 유지하고 12종 × 3단계 전체의 완전히 가려진 내부 삼각형만 제거했다. 이 폴더의 36 GLB가 실제 납품 파일이며 기존 원본은 보존했다.

## 결과와 파일

'''+ '\n'.join(stage_table)+'''

- [모든 유형·단계의 삼각형·정점·bytes](reports/STATS.md), [기계 판독 통계](reports/optimization.json)
- [36 GLB와 기존 편집 원본 참조가 있는 manifest](reports/manifest.json). 각 항목의 `path`는 새 GLB, `source_path`는 원본 GLB, `editable_blend`와 `editable_scene`은 보존된 해당 단계의 편집 원본이다.
- [원본/최적화 검수 맵](blend/hiddenfaces_review.blend): `ORIGINAL • beginning/middle/final`, `OPTIMIZED • beginning/middle/final`, 최적화 36개 자산 라이브러리.
- [전후 비교 전체 갤러리](renders/GALLERY.md), [최종 원본](renders/whole/final_original.png), [최종 최적화](renders/whole/final_optimized.png)
- [독립 검증](reports/validation.json), [환경 보존 지문](reports/map_preservation.json), [시각 검수 기록](reports/visual_review.json), [픽셀 차이·샘플링 대조](reports/pixel_metrics.json)

14필지 합계는 주택 재사용 세 곳을 반영한 가중 합계다. 실제 exported vertex count이며 실제 GPU 메모리나 드로 호출 수를 뜻하지 않는다. GLB bytes는 실제 파일 길이다.

## 제거 기준

부모 검토의 `hidden_faces.py` 알고리즘을 새 폴더에서 전 단계로 확장했다. 원본 스크립트 사본은 `source/reference/`에 텍스트로 보존했고 이전 드라이버는 실행하지 않았다.

1. manifest의 해당 단계 편집 장면만 열었다. 다른 단계·다른 건물·지형을 가림체로 쓰지 않았다.
2. 평가된 부품의 불투명 재질, 닫히고 일관된 방향의 면, 양의 체적, 볼록성·면 평면성을 확인했다. 부품 정점이 실제 원본 GLB 형상과 맞는지도 검사했다. 불확실하거나 비볼록인 부품은 가림체로 사용하지 않았다.
3. 원본 GLB 삼각형의 세 꼭짓점 모두가 한 검증된 볼록 부품 안쪽에 **0.05mm** 여유를 두고 들어간 경우만 제거했다. 경계·부분 겹침·카메라에 안 보이는 후면·밑면이라는 이유로는 지우지 않았다.
4. 유지된 POSITION/NORMAL/COLOR_0 및 모든 정점 속성의 **원시 바이트**를 그대로 복사하고 사용 정점·인덱스만 압축했다. 색이 다른 정점이나 노멀 경계를 합치지 않았다. 노드 변환·재질·extras·루트·축은 보존했다.
5. `reports/mappings/*.json.gz`에 원본 삼각형과 새 인덱스 대응, 제거를 증명하는 부품의 평면과 지문을 남겼다. 독립 검사에서 모든 대응과 제거 조건을 다시 확인했다.

원본 부품의 닫힌 솔리드 검사는 가림체의 유효성을 위한 것이다. 내부 면을 제거한 최종 런타임 메시에는 열린 경계가 있을 수 있으며, 이를 원본 부품 검사와 혼동하지 않았다.

## 원본과 지형 보존

기존 v001/v002 GLB·편집 blend·통합 맵·검토 폴더·고정 샘플 등 보호 입력 '''+str(len(protected))+'''개 파일의 SHA-256이 그대로다. 새 검수 맵은 기존 맵을 읽어 **건물 인스턴스의 자산 참조만 교체**했다. 지형·길·물·나무·공용 소품의 평가된 정점·면·노멀·색·재질·배치 지문과 카메라·조명·색 관리가 원본과 같다. 원본 맵과 새 맵을 새 프로세스로 다시 열어 확인했다.

지형 Decimate 시험본, bevel 제거, 새 LOD, 새 모델, 색·조명 보정은 적용하지 않았다. 기존 편집 원본을 다시 저장하지 않았고 Android·runtime_samples·프로젝트 기획 문서는 수정하지 않았다.

## 검증과 외관 확인

- 36개를 빈 장면에 독립 재가져오기했다. 메시 1개·재질 1개·primitive 1개·텍스처 0개, 불투명 색, 유한한 단위 노멀, 퇴화 삼각형 0개를 확인했다.
- 원본 외곽·지면 기준·피벗·축·스케일 1을 유지했다. L1/L2/L3 공통 최대 외곽은 원본과 같고 14필지 91쌍의 겹침이 없다.
- 14필지 × 3단계 = 42개 주 출입 경로를 실제 최적화 삼각형으로 다시 검사했다. 폭 0.6m, 높이 0.3/0.85/1.5m 광선에서 충돌이 없었다. 엔진 NavMesh나 모든 보조 출입문의 내부 이동 검사는 아니다.
- 실제 납품 GLB를 사용해 시작·중간·최종 전체와 최종 평면의 전후 4쌍, 12종 각각의 L1~L3 정면·후면·측면 36쌍을 새로 렌더했다. 전후 카메라·조명·색 관리·해상도·64 samples·동일 seed를 맞췄다. 전체는 2400×1500, 단품 행은 3000×1600이다. 기존 PNG가 있다는 이유로 렌더를 생략하지 않았다.
- 40개 전후 비교판과 아치·창틀·힙 지붕 모서리·온실·물레바퀴·발코니·전망탑·다락 뒷창의 같은 픽셀 영역 9개를 실제로 열어 검수했다. 검수한 시점에서는 새 실루엣·구멍·색·그림자 변화를 찾지 못했다. 원본의 기존 어두운 접합부는 그대로 보존했다.
- PNG 코드값과 역 sRGB 변환을 거친 표시 기준 선형 RGB 차이를 구분해 기록했다. 비교판과 크롭은 원래 PNG 코드 바이트를 재배열하며 색 보정을 하지 않는다. AgX를 되돌린 장면 방사량으로 표현하지 않는다.

최종 전체 사선도에서 평균 PNG 코드 RGB 절대 차이는 '''+f"{final['mean_png_code_rgb_abs_error']:.8f}"+''', 코드 채널 차이가 0.01을 넘는 픽셀은 '''+f"{final['percent_pixels_over_0_01']:.5f}%"+'''다. 동일 원본의 seed만 바꾼 대조 평균은 '''+f"{noise['mean_png_code_rgb_abs_error']:.8f}"+'''다. 카페·성당·꽃집·물레방앗간 확대 정면과 최종 전체에서 seed 대조 5개를 남겼다. 작은 Cycles 샘플링·수치 차이가 있으므로 픽셀 완전 동일이라고 주장하지 않는다.

이 결과는 3D 파일과 Blender 렌더 검증이다. 앱 교체, 일반 Android 에뮬레이터 성능, Pleos·실차의 프레임 속도·발열·GPU 메모리 개선은 측정하지 않았다.

## 재현

프로젝트 루트에서 아래 순서로 실행한다. 모든 출력은 이 v003 폴더에만 기록한다. Blender 5.2.3 background와 `--python-exit-code 1`을 사용한다.

```text
python -B art/town_season1_v003_hiddenfaces/source/prepare.py
python -B art/town_season1_v003_hiddenfaces/source/run.py optimize
python -B art/town_season1_v003_hiddenfaces/source/run.py map
python -B art/town_season1_v003_hiddenfaces/source/run.py verify
python -B art/town_season1_v003_hiddenfaces/source/run.py render --batch whole
python -B art/town_season1_v003_hiddenfaces/source/run.py render --batch buildings_a
python -B art/town_season1_v003_hiddenfaces/source/run.py render --batch buildings_b
python -B art/town_season1_v003_hiddenfaces/source/run.py render --batch buildings_c
python -B art/town_season1_v003_hiddenfaces/source/run.py pixels
```

새 입력으로 다시 생성했다면 이미지를 직접 열어 `source/reviewed_cases.json`의 검수 기록을 갱신한 뒤 `record_review.py`, `deliver.py`를 실행한다. 시각적으로 의심되는 제거는 `source/retain_triangles.json`에 원본 삼각형 번호를 기록해 유지하고 관련 파일·검증·렌더를 다시 생성한다.
'''
(ROOT/'README.md').write_text(text,encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
