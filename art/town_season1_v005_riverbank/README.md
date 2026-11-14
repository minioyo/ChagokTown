# 차곡마을 — 강둑 소량 돌·풀 마감 v005

2026-11-11. 요청한 **강둑 몇 곳의 낮은 돌·짧은 풀**만 실제 Blender 3D 소품으로 추가했다. v004의 마을 구도·건물 비례·정리된 지붕 톤을 사용한다. 강변 5곳에 돌 12개와 작은 풀 묶음 10개를 두고, 돌 크기·회전·풀 개수에 차이를 주었다. 연속 돌담이나 풀띠 없이 빈 강변을 충분히 남겼다.

- [최종 전체 전후](renders/comparisons/whole_final_comparison.png) · [강둑 확대 전후](renders/comparisons/riverbank_upper_comparison.png) · [방앗간 확대 전후](renders/comparisons/riverbank_mill_comparison.png)
- [시작 전후](renders/comparisons/whole_beginning_comparison.png) · [중간 전후](renders/comparisons/whole_middle_comparison.png) · [탑뷰 전후](renders/comparisons/whole_final_top_comparison.png) · [검수 모음](renders/review_contact_sheet.png)
- [편집 원본](blend/riverbank_review.blend) · [소품 전용 GLB](exports/riverbank_props_v005.glb) · [최종 맵 manifest](reports/manifest.json) · [배치](reports/placements.json)
- [기하·보존·재가져오기 검사](reports/validation.json) · [실제 통계](reports/model_stats.json) · [팔레트](reports/palette.json) · [시각 검수](reports/visual_review.json) · [납품 파일·렌더 해시](reports/delivery.json)

## 파일과 연결 방법

편집 장면은 `RIVERBANK v005 • beginning`, `RIVERBANK v005 • middle`, `RIVERBANK v005 • final`이다. 세 장면에 같은 `RIVERBANK v005 • sparse stones and short grass` 컬렉션을 연결해 위치·메시를 공유한다. 각 작은 무리는 별도 하위 컬렉션이고, 돌·풀은 의미 있는 오브젝트명과 6개의 재사용 메시로 남겼다. 파일을 열면 v005 최종 장면이 선택되어 있다.

같은 파일의 `AFTER roof tones • …`는 v004 비교 입력이고, `BEFORE v003`, `ARCHIVE v002`는 이전 버전 참고다. v005 최신 장면과 혼동하지 않는다. `LIBRARY • riverbank props GLB`는 병합된 소품 내보내기 장면이다.

소품 GLB에는 **강둑 소품만** 들어 있다. 건물·지형·물·길·나무·카메라·조명·텍스처는 포함하지 않았다. 앱 연결은 수행하지 않았다. 나중에 기존 전체 맵과 함께 아래 변환으로 붙인다.

| 항목 | 값 |
|---|---|
| 단위 | 1 unit = 1 m |
| Blender | XY 지면, +Z 위, 기존 마을 원점 (0,0,0) |
| glTF | +Y 위, 위치 변환 `(x, elevation, -y)` |
| GLB 루트 | 원점 (0,0,0), 회전 identity, scale (1,1,1) |
| 소품 위치 | 기존 마을의 절대 배치를 메시 정점에 베이크함. 개별 무리 중심에 다시 놓지 않음 |
| 개별 편집 정보 | `reports/placements.json`의 Blender 월드 행렬·원점·축척·지면 높이 |

`manifest.assets`와 `manifest.layout`은 **v004 manifest와 완전히 동일**하다. 실제 건물 경로는 여전히 `assets[].path`다. v004 파일 24개와 v003 파일 12개를 참조하며, 건물을 새 버전 폴더로 복제하지 않았다. 승계된 `changed_assets`, `unchanged_assets`, 각 건물의 `changed` 등은 v004 지붕 색 변경 이력이다. 이번 v005에서 변경한 건물은 0개다.

## 추가 비용과 마감

| 실제 소품 GLB | 값 |
|---|---:|
| Triangles | **1,330** |
| 내보낸 정점 | **1,488** |
| 병합 전 위치 정점 합계 | 763 |
| 런타임 메시 / 재질 / primitive | **1 / 1 / 1** |
| 텍스처 | 0 |
| 파일 크기 | **62,964 bytes** (약 61.5 KiB) |
| 편집 오브젝트 / 고유 메시 | 22 / 6 |

기존 `Stone shade`, `Wall stone`, `Leaf`, `Leaf light`의 실제 선형 RGB를 재사용한다. 불투명 `COLOR_0`, metallic 0, roughness 0.78, 뒷면 컬링을 사용한다. 외부 모델·텍스처·생성 이미지·유료 생성 서비스는 사용하지 않았다.

저면수의 둥근 돌 3종과 입체 풀 묶음 3종을 재사용했다. 실제 저장된 지형 메시를 레이캐스트해 수면 높이와 강둑 경사를 찾았다. 돌은 지면에 일부 묻히고, 풀의 각 밑면은 마른 지면 아래에 접지한다. 강둑을 맞추기 위한 지형 수정은 없다. 방앗간과 물레바퀴 앞뒤의 Blender Y -8.2~-2.0 m 구간은 비워 두었다.

## 검증 범위

- 입력 v004 blend와 원본·최종 건물 GLB를 포함한 **보호 입력 570개**의 작업 전후 SHA-256 일치를 확인했다. [입력 해시 목록](reports/protected_inputs.json).
- 저장된 v005 blend를 별도 Blender background 프로세스로 다시 열었다. 세 성장 장면의 기존 지형 정점·삼각형·노멀·색·재질, 강 폭·모양·물색·높이, 길·나무·공용 소품·건물 배치, 카메라·조명·노출·색 관리·해상도 지문이 v004 기준과 같다.
- 최종 건물 36개를 실제 manifest 경로에서 새로 가져와 저장 장면의 자산과 대응을 확인했다. 모든 비교 렌더는 이 새 건물 입력과 최종 소품 GLB 재가져오기 결과로 만들었다.
- 소품 GLB의 유한 단위 노멀, 면 방향, 불투명 색, `COLOR_0`, 텍스처 0개, 루트·축·축척, 퇴화 삼각형 0개를 확인했다. GLB 재가져오기 후 위치·노멀 오차 0, 선형 RGB 최대 오차 약 8.94e-8이다. 편집 부품을 병합할 때 돌의 smooth normal은 재계산되며, 재가져오기 비교는 실제 최종 병합 GLB를 기준으로 한다.
- 풀 뿌리의 실제 지면 접촉과 마른 위치, 돌의 매립·노출을 검사했다. 세 장면의 실제 건물 **34개 인스턴스** 및 기존 길·골목·광장 **18개 메시**와 소품 사이에 삼각형 교차가 없다. 시작 장면은 건물 일부만 있으므로 42개 검사로 표시하지 않는다. 이는 메시 검사이며 차량이나 게임 이동 테스트는 아니다.
- 최종·시작·중간·탑뷰 전체 4쌍과 강둑·방앗간 확대 2쌍, 총 **12개 새 렌더**를 만들었다. 각 쌍은 동일 카메라·조명·해상도, Cycles 64 samples, seed 71, denoising, adaptive sampling off다. 전체는 2400×1500, 확대는 1800×1500이다. 확대와 탑뷰의 검수 카메라는 복제본이며 저장된 원본 카메라를 변경하지 않았다.
- 비교판은 동일 크기의 BOX 축소·배열과 제목만 사용한다. 색 보정하거나 그림 위에 소품을 덧그리지 않았다. 최종 육안 판정과 확인한 파일 해시는 `visual_review.json`, `delivery.json`에 기록한다.

변경 파일은 이 v005 폴더 안에만 있다. 기존 버전·검토 파일·docs·Android·runtime_samples는 수정하지 않았다. **Android 적용, Pleos·실차 성능·메모리·발열·재미 검증은 이번 범위가 아니다.** 이 면 수와 파일 크기를 실차 성능 보장으로 해석하지 않는다.

## 재현

Blender **5.2.3 LTS**로 실행했다. 기존 생성 드라이버는 실행하지 않는다. 아래 명령은 프로젝트 루트의 PowerShell에서 이 버전 파일만 생성한다. 각 명령이 성공한 다음 다음 명령을 실행한다.

```powershell
$blender = 'C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
$taskRoot = 'art/town_season1_v005_riverbank'
& $blender --background --python-exit-code 1 --python "$taskRoot/source/build.py"
& $blender --background --python-exit-code 1 --python "$taskRoot/source/verify.py"
& $blender --background --python-exit-code 1 --python "$taskRoot/source/render.py" -- preview
& $blender --background --python-exit-code 1 --python "$taskRoot/source/render.py" -- whole
& $blender --background --python-exit-code 1 --python "$taskRoot/source/render.py" -- details
python -B "$taskRoot/source/deliver.py"
```

`scene_checks.py`와 `glb.py`는 v004의 읽기·지문·검증 유틸리티를 이 폴더에 복사한 것이다. 이전 버전 생성 코드를 실행하지 않는다. `probe.py`와 `reports/probe.json`은 작업 전 실제 장면·지형 조사 기록이다. `protected_inputs.json`은 작업 시작 전에 캡처한 입력 해시 목록이므로 재현 시 새로 덮어쓰지 않는다. 재생성한 파일을 다시 직접 열어 시각 검수하고 새 해시를 기록해야 한다.
