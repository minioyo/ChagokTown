# 차곡마을 · 지붕 패치 대비 정리 v004

2026-11-11. 사용자가 밝은 낱장 기와 때문에 낡고 덧댄 듯한 인상을 지적해, v003 내부 면 제거본 위에서 **밝은 기와의 COLOR_0 RGB만** 기본 지붕색에 가깝게 조정했다. 건물별 청록·살구·올리브·갈색·보라 계열과 기와 형상·분할은 유지했다.

- **수정 GLB 24개 / v003 그대로 참조 12개 / 전체 36개 연결.** [manifest](reports/manifest.json)의 `path`가 최종 파일이다. `source_path`는 v003 비교 입력이다. 미수정 12개를 새 파일인 것처럼 복제하지 않았다.
- [전체 수정 렌더](renders/whole/final_after.png), [작은 화면 전후 비교](renders/comparisons/whole_final_overview.png), [모든 단계·지붕 확대 갤러리](renders/GALLERY.md)
- [별도 검수 맵](blend/roof_tones_review.blend): `BEFORE v003 • beginning/middle/final`, `AFTER roof tones • beginning/middle/final`, 두 버전의 36개 자산 라이브러리. `ARCHIVE v002`는 이전 검수 맵에 있던 참고 장면이다.
- [색·부품 기록](reports/PALETTE.md), [정확한 부품별 float RGB·정점 번호](reports/roof_changes.json), [독립 검증](reports/validation.json), [시각 검수](reports/visual_review.json)

## 색과 수정 범위

기본색과 밝은 칸의 차이를 선형 RGB에서 기존의 **10%**만 남겼다. 화면 명도 대비를 수치로 90% 줄였다는 뜻은 아니다. 사각형 패치가 먼저 튀지 않되 입체 기와의 선은 남기는 강도다.

| 밝은 기와 역할 | 기본색 | 이전 밝은색 | 수정 밝은색 |
|---|---|---|---|
| Butter | #BC945A (Brass) | #E9CB89 | #C19B60 |
| Clay light | #BA6555 (Clay) | #D18468 | #BC6957 |
| Roof olive light | #7B805B (Roof olive) | #939575 | #7E825E |
| Roof russet light | #956A55 (Roof russet) | #AE8263 | #986D57 |
| Roof slate light | #4A716C (Roof slate) | #688B7D | #4E746E |
| Teal light | #427B78 (Teal) | #59908A | #457D7A |

수정 유형은 성당·여관·농가·방앗간·빵집·꽃집·주택·회관이다. 패치가 없는 서점·카페·잡화점·작업장은 유지했다. HEX는 표시용 반올림이며 실제 파일은 float RGB를 저장한다.

원본의 실제 단계 편집 장면에서 `Roof • tile panel`, `Roof • broad tile`, `Roof • broad tile colour` 부품을 식별했다. 평가된 부품의 위치와 재질색을 실제 v003 GLB 정점에 대응하고, 수정 정점이 다른 부품과 공유되지 않으며 해당 삼각형도 같은 기와 부품에 속하는지 검사했다. 색 값 전체 치환을 하지 않았다.

새 RGB 외에는 **GLB의 모든 바이트가 v003과 동일**하다. POSITION·NORMAL·인덱스·정점 수·삼각형 수·루트·축·스케일·재질·primitive·텍스처 수·파일 길이를 유지했다. 벽·문·창·처마·용마루·소품 색을 바꾸지 않았으며 숨은 면을 되살리거나 bevel/Decimate를 적용하지 않았다. 편집 원본은 그대로 보존했고 `editable_blend`/`editable_scene`과 색 오버레이 소스로 변경을 재현한다.

## 검증과 판단

- 36개 전후 자산의 색 범위를 원본 편집 부품에서 독립적으로 다시 계산하고, 허용한 기와 RGB 바이트 이외의 차이가 없음을 확인했다. 고유 36개 합계는 **115,877 triangles / 157,565 exported vertices**로 v003과 같다.
- 최종 납품 파일 36개와 비교 입력 36개를 새로 가져와 저장된 검수 맵의 실제 자산 데이터와 일치하는지 검사했다. 불투명 메시 1개·재질 1개·primitive 1개·텍스처 0개, 유한 단위 노멀·퇴화 삼각형 0개를 유지했다.
- 시작·중간·최종 장면의 지형·길·강·나무·공용 소품 메시·정점색·재질·배치, 카메라·조명·노출·색 관리 지문이 v003과 같다. 형상이 동일하므로 v003의 외곽·접근로 검증을 승계하며 이를 이번 새 엔진 이동 검사로 표현하지 않는다.
- v001/v002/v003·감사·고정 샘플 등 보호 입력 493개 SHA-256이 그대로다. 이 새 폴더 안에서만 파일을 만들었다.
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
