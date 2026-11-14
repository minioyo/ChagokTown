"""Index the verified art delivery without writing outside this revision."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read('reports/validation.json');assert v['passed']
assert all(sha(ROOT/p)==h for p,h in v['validated_files'].items()),'Validation is stale'
render=read('reports/renders_final.json');assert render['map_sha256']==sha(ROOT/'blend/integrated_village.blend'),'Render is stale'
assert all(sha(ROOT/r['path'])==r['sha256'] for r in render['images'])
protected=read('reports/protected_art.json');assert all(sha(ART/p)==h for p,h in protected.items())
for source,target in [('03_season_final.png','05_v001_before_oblique.png'),('04_season_final_top.png','06_v001_before_top.png')]:
    assert sha(ART/'town_season1_v001/renders'/source)==sha(ROOT/'renders'/target)
manifest=read('reports/manifest.json');manifest['coordinate_system']={'units':'metres','blend_up':'+Z','blend_front':'-Y','glb_up':'+Y','glb_front':'+Z','layout':'Blender XY; glTF coordinates are (layout_x, elevation, -layout_y)'}
for asset in manifest['assets']:
    asset['editable_blend']='town_season1_v002_integrated/blend/integrated_models.blend' if asset['changed'] else 'town_season1_v001/blend/season1_models.blend'
    asset['editable_scene']=f"EDIT • {asset['type']}_level_{asset['level']}"
(ROOT/'reports/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
stats=read('reports/model_stats.json')['models'];previous=json.loads((ART/'town_season1_v001/reports/model_stats.json').read_text())['models'];env=read('reports/environment.json')
types=['cafe','house','florist','bakery','bookshop','town_hall','grocer','workshop','cathedral','inn','watermill','farmstead']
labels={'cafe':'카페','house':'주택','florist':'꽃집','bakery':'빵집','bookshop':'서점','town_hall':'마을회관','grocer':'잡화점','workshop':'작업장','cathedral':'성당','inn':'여관','watermill':'방앗간','farmstead':'농가'}
table=['| 종류 | L1 삼각형 | L2 | L3 | 파일 |','|---|---:|---:|---:|---|']
for kind in types:
    data=stats if kind+'_level_1' in stats else previous
    nums=[str(data[f'{kind}_level_{n}']['runtime']['triangles']) for n in (1,2,3)]
    table.append('| '+labels[kind]+' | '+' | '.join(nums)+' | '+('이 폴더의 exports/' if data is stats else 'v001 원본 참조')+' |')
images=['01_beginning.png','02_middle.png','03_final_oblique.png','04_final_top.png','05_v001_before_oblique.png','06_v001_before_top.png']+[f'07_{k}_levels.png' for k in types[:8]]
assert all((ROOT/'renders'/p).exists() for p in images)
summary={'status':'Art implementation and Blender verification complete; user selection pending','types':12,'plots':14,'changed_glbs':24,'unchanged_referenced_glbs':12,
 'all_building_world_scales':[1,1,1],'primary_door_stage_cases':42,'maximum_stage_overlap_pairs':0,'minimum_maximum_hull_gap_m':v['minimum_max_hull_gap_m'],
 'reused_trees':env['reused_tree_groups'],'new_trees':0,'protected_old_files':len(protected),'images':[{ 'path':'renders/'+p,'sha256':sha(ROOT/'renders'/p)} for p in images]}
(ROOT/'reports/delivery.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
text='''# 차곡마을 시즌 1 · 통합 배치 v002

2026-11-10. 14채 전체 재배치와 5단계의 문·층·월드 스케일 통일을 함께 구현한 아트 후보본이다. 사용자 최종 선택과 앱 적용은 별도다.

## 먼저 볼 파일

- [최종 전체 사선도](renders/03_final_oblique.png), [최종 전체 평면도](renders/04_final_top.png)
- 같은 카메라의 [시작 8채 L1](renders/01_beginning.png) → [중간 12채 L2](renders/02_middle.png) → [최종 14채 L3](renders/03_final_oblique.png)
- v001 원본 [이전 사선도](renders/05_v001_before_oblique.png), [이전 평면도](renders/06_v001_before_top.png). 원본 PNG를 바이트 그대로 복사했다.
- [편집 가능한 24개 모델 원본](blend/integrated_models.blend), [실제 GLB로 구성한 전체 마을](blend/integrated_village.blend), [8종 단계별 검토 장면](blend/normalized_levels.blend)
- [36개 자산 경로·해시·14필지 배치 manifest](reports/manifest.json), [검증 결과](reports/validation.json), [단계별 출입 경로](reports/access.json)

## 배치와 치수

기존 8채의 좌표·회전·축소 비율을 해제하고 14채 모두 새로 배치했다. 여관·주택·회관·상점을 성당 앞까지 이어 붙이고 작은 공용 마당 두 곳과 골목을 두었다. 농가와 방앗간은 양쪽 가장자리에서 이웃 지붕·작업마당·공용 길과 이어진다. 기존 지형·길을 새 배치에 맞춰 다시 만들었다.

모든 건물 인스턴스의 월드 스케일은 (1,1,1)이다. 일반 문 패널은 폭 0.8m·높이 1.6m이며, 주택 발코니 문도 같은 치수다. 작은 건물은 폭·깊이·층수로 구분한다. 일반 층 간격은 2m 기준이며 편집 원본의 실제 창 중심 간격도 측정했다. 성당의 큰 정문·본당·종탑은 기존의 의도된 예외로 유지했다. 농가의 넓은 헛간 문과 빵집 오븐 창은 주 출입문 규격 대상이 아니다.

빵집의 올리브색 지붕, 서점의 따뜻한 벽과 뾰족한 작은 전망탑을 유지했다. 카페 차양·현관 앞 화분·벤치 위치를 출입 공간에 맞췄고 잡화점 뒤쪽 창은 실제 다락 벽에 붙였다. 창의 갈색 받침 판과 텍스트 텍스처는 사용하지 않는다.

첫 전체 배치는 나무 없이 사선·평면으로 검토했다. 최종본은 기존 15그루 중 8그루만 가장자리에 재사용했으며 새 건물·나무 종류를 추가하지 않았다. 시작·중간·최종은 아트 성장 비교 예시이고 공용 길은 예정 필지까지 먼저 놓여 있다. 게임의 해금·경제 규칙을 정의하지 않는다.

## 모델과 축

이 폴더의 `exports/`에는 정규화한 8종 × 3단계 = 24 GLB가 있다. 성당·여관·방앗간·농가의 12 GLB는 변경하지 않고 v001 파일을 manifest에서 참조한다. 그 4종의 편집 원본은 [v001 모델 blend](../town_season1_v001/blend/season1_models.blend)다. 마을 blend 안에는 36개 실제 GLB의 메시가 포함되어 있다.

Blender 좌표는 미터, Z-up, 정면 -Y, 피벗은 지면 원점이다. GLB는 표준 Y-up으로 내보냈으며 정면은 +Z다. 배치 JSON은 Blender XY를 사용하므로 glTF 공간으로 옮길 때 `(x, 높이, -y)`로 읽는다. 타입별 L1~L3 공통 최대 외곽은 [final_layout.json](reports/final_layout.json)에 있고 각 변경 GLB의 extras에도 공통 배치 범위를 기록했다.

'''+ '\n'.join(table)+'''

## 확인한 범위

- Blender 5.2.3에서 모델 원본과 마을을 새 프로세스로 다시 열었다.
- 변경 GLB 24개를 독립 재수입했다. 각 파일은 메시 1개·머티리얼 1개·primitive 1개·COLOR_0·불투명·텍스처 0개다.
- 원본 구성 요소의 닫힌 면·바깥 방향, 유한한 단위 법선, 퇴화 삼각형 0개, 재수입 후 색상·범위·지면 원점·스케일 1을 확인했다. 모든 단계가 4k/6k/8k 삼각형 예산 안이다.
- 실제 직사각형 창의 뒤쪽에 벽이 있는지도 검사했다.
- 14필지의 L1~L3 합집합 최대 외곽을 사용해 91쌍을 검사했다. 겹침 0쌍, 최소 분리 간격 약 0.406m다. 이 값은 지붕·소품까지 포함한 외곽 간격이며 골목의 보행 폭과 다르다.
- 주 출입구 14곳 × 3단계 = 42경로를 공용 골목까지 연결했다. 실제 재수입 메시를 대상으로 폭 0.6m, 높이 0.3/0.85/1.5m의 광선 검사를 통과했다. 엔진 NavMesh나 모든 보조문·헛간 내부 이동을 검증한 것은 아니다.
- 건물 피벗과 재사용 나무의 지면 접촉을 확인했다.
- 전후 사선도는 v001의 카메라·조명·노출·감마를 유지했고, 시작·중간·최종도 같은 48m 정사영 카메라다. 전후 평면도는 같은 58m 정사영 카메라다. 2400×1500 전체 화면이며 강한 심도·줌·크롭을 사용하지 않았다.
- 보호 대상 기존 아트 259개 파일의 SHA-256은 그대로다. Android·runtime_samples·프로젝트 기획 문서는 수정하지 않았다.

모델의 아트 검증 결과다. 일반 에뮬레이터·Pleos·실차·앱 런타임 성능·재미 검증 결과를 의미하지 않는다.

## 단계별 이미지

'''+ '\n'.join(f'- [{labels[k]} L1 → L2 → L3](renders/07_{k}_levels.png)' for k in types[:8])+'''

## 재생성

프로젝트 루트에서 다음을 순서대로 실행한다. `source/run.py`가 설치된 Blender를 background 모드로 실행한다. 기존 입력 폴더는 읽기 전용으로 취급한다.

```text
python -B art/town_season1_v002_integrated/source/prepare.py
python -B art/town_season1_v002_integrated/source/adapt_legacy.py
python -B art/town_season1_v002_integrated/source/run.py models
python -B art/town_season1_v002_integrated/source/run.py map
python -B art/town_season1_v002_integrated/source/run.py verify
python -B art/town_season1_v002_integrated/source/run.py render
python -B art/town_season1_v002_integrated/source/run.py render --qa
python -B art/town_season1_v002_integrated/source/deliver.py
```

`source/adapt_legacy.py`는 기존 제작 파일에서 빌더 함수만 복사해 치수를 수정한다. 이전 드라이버나 파일 쓰기 코드는 실행하지 않는다. 모든 수정·출력은 이 v002 폴더 소유다.
'''
(ROOT/'README.md').write_text(text,encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='images'},ensure_ascii=False))
