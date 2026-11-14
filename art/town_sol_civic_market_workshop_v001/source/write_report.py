"""Write delivery index and immutable-export handoff after final file/visual checks."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
v=json.loads((ROOT/'reports/validation.json').read_text())
stats=json.loads((ROOT/'reports/model_stats.json').read_text())
assert v['all_passed'] and not v['preview_only'] and len(v['models'])==9
labels={'town_hall':'마을회관','grocer':'식료품점','workshop':'공방'}
rows=[];manifest={}
for key,m in v['models'].items():
    p=ROOT/'exports'/f'{key}.glb'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
    kind=key.rsplit('_level_',1)[0];level=int(key[-1]);dim=m['dimensions_m']
    rows.append(f"| [{labels[kind]} L{level}](exports/{key}.glb) | {m['triangles']:,} | {m['bytes']:,} | {dim[2]:.3f} |")
    manifest[key]={'path':str(p),'bytes':m['bytes'],'sha256':m['sha256'],'triangles':m['triangles'],'height_m':dim[2]}
pics=['01_town_hall_levels.png','02_grocer_levels.png','03_workshop_levels.png']
pics += ['style_'+kind+'_with_cafe.png' for kind in labels]
pics += [key+'.png' for key in v['models']]
pics += [kind+'_level_3_back.png' for kind in labels]
assert len(pics)==18 and all((ROOT/'renders'/p).is_file() for p in pics)
assert (ROOT/'reports/visual_review.md').is_file()
text='''# 차곡마을 — 마을회관·식료품점·공방 v001

2026-11-09. 고정 8개 부지의 첫 마을에 추가할 건물 3종 × 3단계, 실제 모델 9개. 기존 5종과 전체 마을의 배치·길·광장·조경은 부모 세션의 소유이며 이 폴더에서는 수정하지 않았다. 본 작업은 아트 제작이고 시설 용도의 생산경제·Android 기능을 추가하지 않는다.

![마을회관 단계](renders/01_town_hall_levels.png)

## 마을 전체에서 맡는 역할

- **마을회관:** 뒤쪽 중심의 작은 랜드마크. 황토색의 두꺼운 가로 박공지붕, 중앙 출입문과 좌우 창으로 대칭을 잡았다. 작은 커뮤니티 홀 → 벤치가 있는 지붕 현관 → 위층과 작은 종탑. 시계·숫자·문자·깃발 텍스트는 없다. 최고 높이는 5.6 m 안이다.
- **식료품점:** 넓고 낮은 가게. 따뜻한 살구 벽과 녹색의 낮은 단일 경사 지붕, 굵은 사과·호박 상자를 사용한다. 작은 가게 → 양쪽 판매대와 넓은 차양 → 한쪽에만 높아진 저장 공간. 중앙 문 앞을 과일 상자나 기둥으로 막지 않는다. 최고 높이는 4.2 m 안이다.
- **공방:** 연보라색 비대칭 박공지붕과 단순한 망치 표식. 작은 작업집 → 지붕 작업대와 소형 모루 → 위층과 낮은 별채. 기존 카페·빵집과 다른 비대칭 실루엣이다. 최고 높이는 4.4 m 안이다.

팔레트는 기존 세트를 그대로 재사용했다. 지붕은 `Brass #BC945A` / `Leaf dark #58785C` / `Plum #AE7FAD`로 마을의 청록·테라코타 지붕 사이에 색을 더했다. 아이보리 창틀, 청록 문과 불투명 유리, 낮은 분할 수의 부드러운 모서리는 공통이다. 기존 카페보다 소품 수를 적게 유지했고 건물별 용도와 성장 실루엣을 먼저 읽게 했다.

전체 마을의 부모 프리뷰 `art/town_layout_v001/renders/preview_town_mature.png`를 읽기 전용으로 열어 새 3종의 색과 높이가 기존 5종 사이에서 구분되는지 확인했다. 최종 전체 마을 배치의 승인·검증은 부모 세션의 범위다.

## 납품물

- [부품별 편집 Blender 원본](blend/chagok_sol_civic_market_workshop_v001.blend): 단계 비교 3개 + 카페 스타일 비교 3개 + EDIT 9개 + RUNTIME 9개, 총 24개 장면. EDIT의 의미 있는 이름과 bevel을 보존했다. 편집 원본과 런타임은 동일한 미터 축척과 형태다.
- 단계 비교: [마을회관](renders/01_town_hall_levels.png) / [식료품점](renders/02_grocer_levels.png) / [공방](renders/03_workshop_levels.png).
- 카페와 같은 축척: [마을회관](renders/style_town_hall_with_cafe.png) / [식료품점](renders/style_grocer_with_cafe.png) / [공방](renders/style_workshop_with_cafe.png). 각 비교는 새 건물 L1 · 기존 카페 L3 · 새 건물 L3 순서다.
- 개별 사선 9장과 최고 단계 뒤쪽 3장: [renders](renders). 최종 납품 GLB를 재가져와 만든 총 18장이다.

| 최종 GLB | triangles | bytes | 높이 m |
| --- | ---: | ---: | ---: |
'''+ '\n'.join(rows)+'''

모두 **1 mesh / 1 material / 1 primitive**, `COLOR_0` 정점색, 불투명, 금속성 0, 거칠기 0.68, 뒷면 컬링, 텍스처·외부 이미지 0개다. 상한 4,000 / 6,000 / 8,000 triangles 이내이며 경량 예산을 채우기 위해 세부를 늘리지 않았다. 메시 하나 안의 닫힌 조립 부품은 여러 연결 성분으로 남는다. Boolean으로 내부 면까지 제거한 단일 연속 표면이라는 뜻은 아니다.

## 배치 계약과 검사

Blender: **1 unit = 1 m, +Z 위, 정면 -Y, 루트 (0,0,0), scale (1,1,1)**. 모든 단계가 같은 **XY (-2.4,-3.2)~(2.4,1.6) m** 부지 안이다. 처마·별채·과일 상자·현관도 범위 안이다. 문 앞의 보행 접근 공간을 남기고 소품은 양옆으로 놓았다. 정확한 충돌체·경로 찾기는 이 아트에 포함하지 않는다.

- 별도 프로세스에서 `.blend` 재열기와 GLB 9개 각각의 빈 장면 재가져오기 통과.
- 원본의 닫힌 부품·일관된 면 방향·양의 체적·유한한 단위 길이 노멀·퇴화 삼각형 0개 확인.
- 최종 GLB 원시 NORMAL 데이터와 재가져온 노멀의 유한성/단위 길이, 퇴화 삼각형 0개 확인.
- 좌표와 삼각형 방향, 팔레트 집합뿐 아니라 **각 삼각형 모서리의 색 배정**을 원본과 비교해 유지됨을 확인했다. 바닥·축척·루트·부지·높이 상한도 통과했다.
- 문자 객체·갈색 창문 덧판은 없다. 기존 창틀 교차점의 깊이 오프셋과 얇은 판 bevel 제한을 독립 `geometry.py`에서 유지했다.
- 이전 아트 파일 '''+str(v['protected_files_unchanged'])+'''개의 SHA-256 일치. 부모 세션이 수정하는 docs는 보존 검사에서 제외했고, 이 세션은 docs를 쓰지 않았다.
- 실제 최종 렌더를 열어 확인한 내용: [시각 검수](reports/visual_review.md).

원자료: [최종 검증](reports/validation.json), [통계](reports/model_stats.json), [팔레트](reports/palette.json), [기존 에셋 보존](reports/protected_files_sha256.json), [생성 로그](reports/build.log), [렌더 로그](reports/render.log).

## 부모 세션으로 넘기는 최종 상태

README 생성 시 GLB 9개의 실제 SHA-256을 최종 검증 기록과 다시 대조했다. [DELIVERY_READY.json](reports/DELIVERY_READY.json)에 고정된 파일 경로·해시·크기를 기록했다. 이 납품 이후 자동으로 exports를 다시 생성하지 않는다. 추가 수정 요청이 오면 기존 검증/마을 장면의 해시를 갱신해야 한다.

이 검증은 3D 파일·오프라인 렌더에 한정된다. Android 연결·일반 에뮬레이터 성능·Pleos·실차 프레임/메모리/발열·사용자 재미 검증은 수행하지 않았다. 엔진의 그림자/깊이 패스까지 하나의 draw call이라고 보장하지 않는다.

## 소스와 재현

- 요청: [제작 브리프](reports/production_brief.md). 요청된 모델/effort는 GPT-6.1 Sol / xhigh, 제작은 Codex와 Blender 5.2.3 LTS.
- 기준: [TOWN_ART_STYLE.md](../../docs/TOWN_ART_STYLE.md), [빵집·책방](../town_sol_bakery_bookshop_v001/README.md), [카페 v003](../town_cafe_v003/README.md).
- 독립 사본을 바탕으로 새 건물·박공 마감·접지·종탑을 구현한 [build_set.py](source/build_set.py), [형태 함수](source/geometry.py), [재가져오기·검증·렌더](source/render_verify.py), [기록 생성](source/write_report.py).
- 외부 모델이나 텍스처를 다운로드하지 않았다. 모든 건물과 그림 표식은 실제 메시다. 이전 버전 스크립트를 실행해 기존 산출물을 다시 생성하지 않았다.

```powershell
& 'D:/Project/Etc/ChagokTown/art/town_sol_civic_market_workshop_v001/source/run.ps1'
python -B 'D:/Project/Etc/ChagokTown/art/town_sol_civic_market_workshop_v001/source/write_report.py'
```

모든 Blender 호출에 `--python-exit-code 1`을 사용한다. `run.ps1 -Preview`는 별도 preview 렌더/검증만 만든다. 인자 없는 실행이 최종 검증이다. 재생성은 이 폴더의 생성 산출물을 덮어쓰므로 수동 편집 사본은 별도로 보존한다. 이미 마을에 배치한 모델을 재생성하면 부모 장면의 해시 기준도 새로 확인해야 한다.
'''
(ROOT/'README.md').write_text(text,encoding='utf-8')
for target in re.findall(r'\]\(([^)]+)\)',text):
    if not target.startswith(('https:','http:')):
        if target=='reports/DELIVERY_READY.json':continue
        assert (ROOT/target).exists(),target
ready={'exports_stable':True,'final_validation_passed':True,'model_count':9,'render_count':18,
       'all_models_visually_reviewed':True,'previous_art_files_unchanged':v['protected_files_unchanged'],
       'android_pleos_vehicle_performance_tested':False,'models':manifest}
(ROOT/'reports/DELIVERY_READY.json').write_text(json.dumps(ready,indent=2),encoding='utf-8')
print('DELIVERY_READY',len(manifest),'models',len(pics),'renders',flush=True)
