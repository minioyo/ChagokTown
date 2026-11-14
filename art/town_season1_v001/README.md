# 차곡마을 — 1시즌 완성형 구성 시안 v001

요청 기준: 2026-11-09. **제작 순서 1~4 완료**, 5(기존 건물까지 전체 비례 정리)와 6(최종 배치·런타임 최적화·앱 연결)은 후속 단계다. 이 결과는 성장 최종 상태의 아트 시안이며 확정 게임맵·사용자 미감 승인·차량 성능 보장을 뜻하지 않는다.

## 선택과 제작 가정

사용자가 선택한 [v003 Compact](../town_layout_v003_density/renders/compact_oblique.png)의 중심 골목과 작은 마당을 기반으로 삼았다. 성당 등 다양한 건물로 시즌 완성형 모습을 먼저 구성하고, 이후 문·층 높이와 폭·지붕 연결감을 정리한다는 순서를 따랐다. [Tiny Glade 사용자 참고](../reference/town_layout_2026_11_09/user_selected_tiny_glade.png)의 따뜻한 돌벽, 높은 중심 지붕, 좁은 골목과 물길을 보며 제작했다.

여관·물레방앗간·농가, 약 14구획, 시작/중간/최종의 건물 수와 단계 조합은 제작 가정이다. 개별 건물 목록·게임 카탈로그 상한·실제 생산 경제·진행 시간표를 새로 확정한 것이 아니다. 후속 해안도시 테마는 제작하지 않았다.

## 1~4 완료 근거

| 순서 | 결과 |
| --- | --- |
| 1. 최소 비례 | 신규 일반 문 패널 실제 0.8 × 1.6 m, 일반 상·하층 창 중심과 층 기준 간격 약 2.0 m. 새 4종 배치 scale `(1,1,1)` 유지. 성당 큰 정문과 높은 신랑·종탑은 의도적 예외. |
| 2. 완성형 덩어리 | [최대 단계 덩어리 사선](renders/00_max_stage_blockout.png)·[평면](renders/00_max_stage_blockout_top.png)을 먼저 제작·검토했다. 성당을 주 랜드마크로 두고 여관/식료품점의 초기 부지 겹침과 지형 가장자리 잘림을 수정했다. |
| 3. 네 종류 × 세 단계 | 부품별 원본과 **신규 GLB 12개**를 완성했다. 모두 단계별 4k/6k/8k 목표 이내이며 별도 예산 예외는 사용하지 않았다. |
| 4. 시즌 성장 비교 | 같은 전체 카메라의 시작 8채·중간 12채·최종 14채, 최종 평면, 중심 가까운 시점, 유형별 3단계 비교가 있다. 전부 실제 GLB를 가져온 장면에서 렌더했다. |

## 건물과 실제 면 수

| 건물 | L1 triangles | L2 triangles | L3 triangles | 공통 최대 부지 W×D m | 보기 |
| --- | ---: | ---: | ---: | ---: | --- |
| 성당 | 2,100 | 5,718 | 6,730 | 7.75 × 9.3 | [3단계 비교](renders/06_cathedral_levels.png) |
| 여관 | 2,316 | 4,140 | 4,532 | 7.6 × 7.95 | [3단계 비교](renders/06_inn_levels.png) |
| 물레방앗간 | 2,580 | 3,944 | 4,776 | 7.65 × 6 | [3단계 비교](renders/06_watermill_levels.png) |
| 농가 | 2,272 | 3,824 | 5,884 | 9.7 × 7.05 | [3단계 비교](renders/06_farmstead_levels.png) |

각 유형은 세 단계의 루트 `(0,0,0)`, +Z 위, 정면 -Y, 자체 최대 부지를 공유한다. 성당 부지는 `(-4,-4.65)~(3.75,4.65)`, 여관 `(-3.8,-4.4)~(3.8,3.55)`, 방앗간 `(-3.45,-3)~(4.2,3)`, 농가 `(-4.85,-3.6)~(4.85,3.45)`다. 4.8 m 정사각형으로 줄이지 않았다. 삼각형 수에는 문·창·별채·물레바퀴·텃밭 등의 해당 단계 구성물이 포함된다.

- **성당:** 작은 예배당 → 확장 신랑·낮은 측랑·작은 종탑 → 높은 종탑·주 지붕·뒤쪽 공간. 최종 종탑 꼭대기는 로컬 약 11.09 m다. 정문 패널은 L1 0.9 × 1.9 m, L2/3 1.3 × 2.5 m이며 측문은 일반 기준이다. 신랑은 큰 단일 공간이므로 일반 집의 반복 층 높이를 강제하지 않았다.
- **여관:** 작은 숙박집 → 넓은 2층 본채와 낮은 날개 → 2층 L자 날개와 열린 중정. 문과 층 간격은 유지하면서 폭·점유 형태가 바뀐다.
- **방앗간:** 낮은 작업집과 바퀴 → 낮고 넓은 작업/저장 별채 → 높은 주 건물과 낮은 작업동·짐 싣는 차양. 지도 수면은 -0.40 m로 바퀴 아래 날개가 물에 닿는다. 회전 애니메이션은 만들지 않았다.
- **농가:** 주택·작은 텃밭 → 헛간·작업 차양 → 2층 주택·낮은 저장동·두 번째 텃밭. 농작물은 아트이며 생산 기능은 없다.

문·층 기준과 실제 문 패널 측정은 [모델 통계](reports/model_stats.json), [재열기/재가져오기 검증](reports/validation.json)에 있다. 일반 창틀은 입체적인 옅은 프레임만 사용하며 갈색 받침판과 문자 간판은 없다. 목재는 필요한 지지대·문·바퀴·상자·벤치에 사용했다. 지붕과 돌벽은 큰 색면과 낮은 분할로 표현했다.

## 맵과 성장 예시

Compact의 **8구획 XY·회전·축척은 유지**했다. 최종에는 각 구획을 3단계로 교체하고, 식료품점·마을회관과 신규 네 유형을 이어 총 14구획으로 구성했다. 기존 작은 집 사본을 추가해 수를 채우지 않았다. 성당은 위쪽 언덕의 독립된 목표, 여관은 입구의 넓은 마당, 농가/식료품점은 서쪽 생활 골목, 방앗간은 수로·다리의 목적지다. 중심 마당을 큰 광장으로 넓히거나 균등한 외곽 순환로를 만들지 않았다.

| 장면 | 건물 수 | 건물 triangles | 환경 triangles | 활성 장면 합계 |
| --- | ---: | ---: | ---: | ---: |
| beginning | 8 | 21,904 | 68,212 | 90,116 |
| middle | 12 | 53,682 | 68,212 | 121,894 |
| final | 14 | 85,762 | 68,212 | 153,974 |

환경에는 연속 지형, 기존 나무·소품, 길·계단·옹벽·수로·두 다리가 들어 있다. 합계는 평가된 메시의 실제 삼각형 수이며 사용하지 않는 라이브러리/편집 원본은 제외한다. draw call, FPS, 메모리 또는 실차의 보장 예산으로 환산한 값이 아니다.

| 보기 | 파일 |
| --- | --- |
| 시작 — 8채/L1 | [전체 PNG](renders/01_season_beginning.png) |
| 중간 — 12채/L2 | [전체 PNG](renders/02_season_middle.png) |
| 최종 — 14채/L3 | [전체 PNG](renders/03_season_final.png) |
| 최종 평면 | [PNG](renders/04_season_final_top.png) |
| Compact 중심 가까운 시점 | [PNG](renders/05_compact_centre_close.png) |

세 전체 장면은 2400×1500, **동일 카메라 행렬/회전/위치와 ortho 48 m**, 동일 조명·AgX·노출 0.15·gamma 1·DOF 끔, Cycles 64 samples다. 평면은 `(-1.5,2,55)`, ortho 58 m이며, 중심 가까운 시점은 별도 목표점/ortho 24 m다. 이 두 구역 시점의 확대를 전체 밀도 개선의 근거로 사용하지 않았다. 유형별 비교는 3000×1440이며 각 행 안에서 같은 카메라·1 m 축척을 사용한다.

## 파일·형상·배치 확인

- 편집 원본 `.blend`와 지도 `.blend`를 **별도 Blender 프로세스에서 다시 열었다**. 원본에는 의미 있는 이름의 독립 부품과 12개 편집 장면이 있다.
- 신규 GLB 12개를 빈 장면에 하나씩 재가져왔다. 각각 메시 1개·재질 1개·primitive 1개, `COLOR_0`, opaque, metallic 0, roughness 0.68, 텍스처 0개다. 원시 GLB NORMAL과 재가져온 corner normal의 finite/unit, 퇴화 삼각형 0, 다색 유지, 단위 축척, 축·바닥 높이·경계 일치를 검사했다. 원본 부품도 닫힌 외향 솔리드와 정상 노멀을 확인했다.
- Compact의 빵집 색·책방 탑 변형은 새 [reused_compact](exports/reused_compact/)에 따로 병합했다. 신규 종류/단계 12개에 포함하지 않는다. 기존 형상과 삼각형 수·경계를 보존한 뒤 다시 가져왔으므로 최종 지도 전체가 실제 GLB 기반이다. [변형 보존 기록](reports/reused_compact_variants.json).
- 최대 단계 실제 XY convex hull 기준으로 14구획 **91쌍의 겹침이 0**이다. 새/추가 구획이 관련된 최소 분리축 간격은 약 0.789 m다. [실제 외곽·배치](reports/final_layout.json), [독립 재검사](reports/verified_final_layout.json).
- 14개 주 현관의 포장 연결을 현재 건물 메시의 중심·양옆 세 레이로 확인했다. 폭/높이는 문 축척을 따랐고 [현관 기록](reports/entrance_access.json), [길 네트워크](reports/path_network.json)에 저장했다. 지형 경사를 따르는 국소 검사이며 전체 게임 내 보행 에이전트·내비게이션·상호작용은 검증하지 않았다.
- 각 건물 루트의 지형 접지와 전체 카메라의 모델 잘림 없음도 검사했다. [검증 상세](reports/validation.json). 큰 렌더를 직접 열어 성장 차이와 가림을 확인했고, 성당 L2의 지붕 위 창 돌출, 여관 날개 뒤의 창, 후면 창틀 모서리의 겹친 면, 방앗간 앞 나무 가림, 농가 비교 잘림, 중복 입구 길을 수정했다.
- 재사용 아트 **197개 파일**의 해시가 제작 전후 같다. 부모가 담당하는 문서는 보호 해시에서 제외했다. 이전 산출물·문서·Android 코드와 다른 작업자의 편집을 덮어쓰지 않았다.

## 원본·GLB·소스

- [부품별 편집 원본](blend/season1_models.blend): `EDIT • type_level_n` 장면. 단일 병합 GLB와 별개로 문·벽·지붕·탑·바퀴 등이 남아 있다.
- [지도 원본](blend/season1_map.blend): `Season 1 • beginning / middle / final`, 유형별 `LEVELS • type` 장면. 지형·길은 편집 메시이고 건물은 실제 GLB 컬렉션 인스턴스다.
- [최대 단계 덩어리 원본](blend/season1_blockout.blend): 세부 제작 전 구도 확인 기록.

| 유형 | 1단계 | 2단계 | 3단계 |
| --- | --- | --- | --- |
| 성당 | [L1 GLB](exports/cathedral_level_1.glb) | [L2 GLB](exports/cathedral_level_2.glb) | [L3 GLB](exports/cathedral_level_3.glb) |
| 여관 | [L1 GLB](exports/inn_level_1.glb) | [L2 GLB](exports/inn_level_2.glb) | [L3 GLB](exports/inn_level_3.glb) |
| 물레방앗간 | [L1 GLB](exports/watermill_level_1.glb) | [L2 GLB](exports/watermill_level_2.glb) | [L3 GLB](exports/watermill_level_3.glb) |
| 농가 | [L1 GLB](exports/farmstead_level_1.glb) | [L2 GLB](exports/farmstead_level_2.glb) | [L3 GLB](exports/farmstead_level_3.glb) |

[모델 생성](source/models.py), [형태 함수](source/geometry.py), [12단계 제작/내보내기](source/build_models.py), [지형·공통 장면](source/scene_common.py), [시즌 조립](source/build_map.py), [배치 JSON](source/layout.json), [현관 검사](source/access.py), [검증 소스](source/verify.py), [배경 실행기](source/run.py), [렌더](source/render.py), [사용 팔레트](reports/palette.json).

## 남은 단계

**5. 전체 비례 정리:** 기존 Compact의 0.58~0.90 배율과 문/층 크기는 이번에 고치지 않았다. 신규 일반 문은 1.6 m이나 기존 축소 집의 문은 더 작다. 이 차이를 해결하고 폭·깊이·지붕 높이로 다양성을 만들 때, 기존 중심 구획의 배치도 일부 다시 조정할 수 있다. 외곽 추가 구역은 최대 단계와 접근 공간을 확보했지만 이 배치를 최종 고정 게임맵으로 잠그지 않는다.

**6. 최종 배치·경량화·앱 연결:** 비례 보정 후의 최대 외곽, 출입/선택 가독성, 엔진 재질·조명·그림자 비용, Android/Pleos/실차 성능 검증은 남아 있다. 이번에는 엔진·경제·종교 기능·자동 생산·물레 애니메이션을 구현하지 않았다.

## 재현

프로젝트 루트에서 실행한다. 실행기는 로컬 Blender 경로를 명시하며 `--background --python-exit-code 1`을 사용한다. `prepare`는 기존 아트를 읽고 이 폴더에만 복사한다. 스크립트는 이전 버전의 생성기를 실행하지 않는다.

```text
python -B art/town_season1_v001/source/prepare.py
python -B art/town_season1_v001/source/run.py blockout
python -B art/town_season1_v001/source/run.py models
python -B art/town_season1_v001/source/run.py variants
python -B art/town_season1_v001/source/run.py map
python -B art/town_season1_v001/source/run.py verify
python -B art/town_season1_v001/source/run.py renders --all
python -B art/town_season1_v001/source/run.py renders --preview --backs
python -B art/town_season1_v001/source/write_report.py
```

후면 점검 렌더는 `renders/preview_qa_back_type.png`이며 화면 왼쪽부터 L3/L2/L1이다. 결과 해시·크기는 [산출물 목록](reports/final_artifacts.json), 입력 보호 기록은 [원본 해시](reports/protected_art_sha256.json)에 있다. 모델 생성/재열기/렌더 로그도 `reports/`에 보존했다.
