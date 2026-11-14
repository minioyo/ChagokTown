"""Validate delivered files and write the small density-comparison record."""
import hashlib,json,math,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'town_layout_v002_concepts'
metrics=json.loads((ROOT/'reports/density_metrics.json').read_text())
completion=json.loads((ROOT/'reports/completion.json').read_text())
access=json.loads((ROOT/'reports/entrance_checks.json').read_text())
layouts=json.loads((ROOT/'reports/display_layouts.json').read_text())
sources=json.loads((ROOT/'reports/read_only_sources.json').read_text())
assert completion['blend_reopened'] and completion['independent_blend_reopen_passed'] and not completion['preview']
assert metrics['control']['base_eight_collections_identical'] and metrics['control']['base_eight_scales_identical']

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

artifacts={}
for label in ('baseline','compact','dense'):
    for view in ('oblique','top'):
        path=ROOT/'renders'/f'{label}_{view}.png';data=path.read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n'
        dimensions=struct.unpack('>II',data[16:24]);assert dimensions==(1920,1080)
        artifacts[str(path.relative_to(ROOT))]={'sha256':digest(path),'bytes':len(data),'resolution':dimensions}
        if label=='baseline':assert data==(OLD/'renders'/f'A_{view}.png').read_bytes()
for name in ('Baseline','Compact','Dense'):
    m=metrics[name];assert m['calibration_matches_baseline']
    assert m['instances']==len(layouts[name])
    assert len(m['max_stage_pairs'])==math.comb(m['instances'],2)
    assert all(pair['gap_m']>0 for pair in m['max_stage_pairs'])
assert metrics['Baseline']['tree_count']==metrics['Compact']['tree_count']==metrics['Dense']['tree_count']
assert layouts['Compact']==layouts['Dense'][:8]
for name,count in [('Compact',8),('Dense',16)]:
    assert len(access[name])==count and all(p['clear_of_current_building_meshes'] for p in access[name].values())
for path,sha in sources.items():assert digest(ROOT.parent/path)==sha,path
blend=ROOT/'blend/chagok_density_comparison.blend'
assert blend.is_file() and blend.stat().st_size>100000
artifacts[str(blend.relative_to(ROOT))]={'sha256':digest(blend),'bytes':blend.stat().st_size}
(ROOT/'reports/final_artifacts.json').write_text(json.dumps({'checks_passed':True,'previous_files_unchanged':len(sources),'artifacts':artifacts},indent=2),encoding='utf-8')

rows=[]
for name in ('Baseline','Compact','Dense'):
    m=metrics[name]
    rows.append(f"| {name} | {m['instances']} | {m['center_convex_hull_area_m2']:.3f} | {m['instances_per_100_m2']:.3f} | {m['max_stage_xy_coverage_percent']:.2f}% | {m['building_triangles']:,} | {m['total_visible_scene_triangles']:,} |")
reduction=100*(1-metrics['Compact']['center_convex_hull_area_m2']/metrics['Baseline']['center_convex_hull_area_m2'])
trees=metrics['Baseline']['tree_count']
text=f'''# 차곡마을 v003 — 같은 카메라의 밀도 비교

2026-11-09. **배치 밀도에 관한 비교 시제품**이다. 개별 건물 추가 제작, 앱 통합, 전체 마을 GLB 또는 24개 건물 전체 재검수 결과가 아니다. 최종 마을 채택·차량 성능 검증을 뜻하지 않는다.

## 비교 의도와 통제 조건

- **Baseline:** v002 A 원본 그대로. 사선·평면 PNG를 바이트 단위로 복사했다.
- **Compact:** 같은 8채의 종류·단계·축척·메시·재질·색을 유지하고 위치와 방향만 조정했다. 같은 원본 컬렉션을 직접 공유한다. 작은 공동 마당, 상점 골목과 위쪽 주거 길을 묶고 잔디 간격을 줄였다.
- **Dense:** Compact의 8채 배치를 그대로 유지하고 기존 GLB 사본 8채를 추가했다. 1~3단계 주택, 작은 카페·꽃가게·식료품점으로 지붕·높이·방향을 섞었다. 이 사본은 배경 밀도 실험이며 게임 건물 카탈로그나 경제 결정을 추가하지 않는다.
- 세 장면의 사선 카메라 행렬·회전·위치와 orthographic scale 28 m가 같다. 평면은 위치 `(0, 3, 45)`, 회전 `(0, 0, 0)`, scale 35 m로 통일했다. 1920×1080, Cycles 64 samples, AgX, exposure 0.15, gamma 1, DOF 끔. 자르기·확대·추가 나무로 밀도를 만들지 않았다.
- 조명·월드·색 관리 설정을 각 장면에서 비교했다. 기존 8채의 원본 컬렉션 참조와 축척도 검사했다. v002의 책방 탑/지붕과 빵집 색 변형도 그대로 재사용했다.
- 나무는 세 장면 모두 **{trees}그루**다. Compact/Dense에서 광장 나무·벤치·우물 위치와 소품의 접지 높이를 조정했고 지형·포장·옹벽·계단의 XY를 배치에 맞춰 변형했다. 건물 형상에는 이 변형을 적용하지 않았다. 지형 변형의 모든 삼각 셀은 뒤집힘 없이 유지된다.

## 수치

| 안 | 건물 수 | 중심점 분포 면적 m² | 100 m²당 건물 | 최대 단계 XY 점유율 | 건물 triangles | 장면 triangles |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

`중심점 분포 면적`은 건물 루트 XY의 convex hull 면적이다. 실제 지적 면적이 아니다. Compact는 같은 8채에서 이 면적을 **{reduction:.1f}%** 줄였다. Dense는 Compact의 범위를 주변 골목으로 넓힌 16채 실험이므로 두 안이 같은 면적이라고 주장하지 않는다.

`최대 단계 XY 점유율`은 겹치지 않는 건물별 최대 단계 외곽 convex hull 면적 합 ÷ 이 외곽들을 모두 감싼 convex hull 면적이다. 처마·화분·테라스도 포함하는 보수적 비교값이며 현재 단계의 실제 지붕 픽셀 비율은 아니다. 최대 단계 외곽 면적 합과 전체 군집 면적은 [원자료](reports/density_metrics.json)에 있다. 장면 triangles는 활성 장면의 환경과 실제 건물 인스턴스를 합산한 값이며 사용하지 않는 라이브러리는 제외했다. 최적화 전/후나 런타임 성능 측정값이 아니다.

## 배치·파일 확인

- 4.8 m 정사각 슬롯 대신 이전 검수에서 추출한 건물별 실제 최대 단계 XY 외곽을 사용했다. Baseline 28쌍, Compact 28쌍, Dense 120쌍에서 분리축 간격이 모두 양수다. 최소 간격은 각각 {metrics['Baseline']['minimum_separating_axis_gap_m']:.3f} / {metrics['Compact']['minimum_separating_axis_gap_m']:.3f} / {metrics['Dense']['minimum_separating_axis_gap_m']:.3f} m다.
- Compact 8곳과 Dense 16곳의 현관에서 실제 Path 재질의 기존 포장까지 연결점을 기록했다. 실제 현재 건물 메시 BVH에 중심·양옆 3개 레이를 보내 통과 여부를 검사했다. 새 연결로의 지형 표본 경사 상한을 0.70으로 두고 급격한 옹벽 높이 변화를 피했다. 직선으로 막히는 곳은 건물 옆으로 돌아 연결했다. 작은 집은 문 축척에 맞춰 폭과 높이를 줄였으며 수치는 [현관 연결 기록](reports/entrance_checks.json)에 있다. 이미 포장과 만나는 현관은 매우 짧은 연결이다. 이는 시각 시제품의 국소 연결 검사이며 전체 보행 폭·경사·옹벽 통과·게임 내 내비게이션을 보증하지 않는다.
- `.blend`를 저장한 뒤 다시 열어 Compact/Dense 사선·평면을 렌더했다. 이후 별도 Blender 프로세스에서 다시 열어 8/8/16채, 기존 8채 컬렉션 참조·위치·축척, 카메라, 해상도와 나무 수를 확인했다. [독립 재열기 결과](reports/independent_blend_reopen.json). Baseline의 두 PNG는 v002와 바이트가 같다. 여섯 최종 PNG가 모두 1920×1080인지 검사했다.
- v002와 재사용 GLB **{len(sources)}개 파일**의 해시가 제작 전후 동일하다. [원본 해시](reports/read_only_sources.json), [결과 해시·크기](reports/final_artifacts.json), [실제 카메라·조명 값](reports/calibration.json), [실행 로그](reports/final.log).
- 실제 사선·평면 여섯 장을 열어 군집 차이, 건물 겹침·접지·잘림을 확인했다. 기존 소스/후보와 별도 폴더로 보존했다. 앱·일반 에뮬레이터·Pleos·실차·재미 검증은 이번 작업에서 하지 않았다.

## 짧은 판정

**밀도는 차이를 만든다.** Compact만으로 넓게 흩어진 단품 전시 느낌이 줄고 하나의 상점 골목과 작은 마당으로 묶인다. Dense는 전경·측면·뒤쪽에 이어지는 지붕 수와 높이 차를 늘려 마을 규모를 읽기 쉽게 한다. 첫 14채 미리보기는 뒤쪽 작은 사본이 많이 가려져 차이가 약했고, 16채로 전경·측면의 기존 단계 사본을 보강했다. 현관이 앞집 뒤를 향하던 추가 주택은 바깥 골목 쪽으로 돌렸다.

다만 Tiny Glade 기준의 건축 비례·풍부한 지붕 형태·지형과 수로의 공간감까지 밀도만으로 얻지는 못했다. Dense의 작은 사본은 주 건물보다 작아 주변 채움으로 읽히며, 평면 점유율도 Compact보다 약 1.3%p만 높다. **같은 8채를 모은 효과와 건물 수를 늘린 효과를 분리해서 판단하는 비교안**으로 보는 것이 맞다.

## 결과와 재현

| 안 | 사선 | 평면 |
| --- | --- | --- |
| Baseline 8채 | [PNG](renders/baseline_oblique.png) | [PNG](renders/baseline_top.png) |
| Compact 8채 | [PNG](renders/compact_oblique.png) | [PNG](renders/compact_top.png) |
| Dense 16채 | [PNG](renders/dense_oblique.png) | [PNG](renders/dense_top.png) |

[편집 원본](blend/chagok_density_comparison.blend)의 `Baseline • v002 A`, `Compact • same eight models`, `Dense • sixteen existing copies` 장면을 선택하면 된다. 건물은 의미 있는 이름의 collection instance라 위치·방향·단계별 원본 컬렉션을 편집할 수 있고, 지형·계단·포장은 메시로 들어 있다. 개별 건물의 부품별 제작 원본은 기존 각 자산 폴더에 보존했다.

[배치 소스](source/layouts.json), [실제 지형 높이를 적용한 배치](reports/display_layouts.json), [배치 생성기](source/plan_density.py), [Blender 제작 소스](source/build_density.py), [실행기](source/run.py), [보고서·검사 소스](source/write_report.py).

프로젝트 루트에서 아래 순서로 실행한다. 기존 v002와 기존 개별 GLB가 입력이며 결과는 이 폴더 안에 쓴다. Blender 실행기는 Windows 로컬 경로를 명시하고 `--background --python-exit-code 1`을 사용한다.

```text
python -B art/town_layout_v003_density/source/plan_density.py
python -B art/town_layout_v003_density/source/run.py
python -B art/town_layout_v003_density/source/write_report.py
```
'''
(ROOT/'README.md').write_text(text,encoding='utf-8')
print(json.dumps({'final_pngs':6,'blend_bytes':blend.stat().st_size,'read_only_source_files':len(sources),'checks':'passed'},ensure_ascii=False))
