# 차곡마을 시즌 1 · 전 단계 내부 면 제거 v003

2026-11-11. 통합 v002의 디자인·구도·비례와 지형을 유지하고 12종 × 3단계 전체의 완전히 가려진 내부 삼각형만 제거했다. 이 폴더의 36 GLB가 실제 납품 파일이며 기존 원본은 보존했다.

## 결과와 파일

| 14필지를 모두 해당 단계로 놓을 때 | triangles 전 → 후 | 실제 exported vertices 전 → 후 | GLB bytes 전 → 후 |
|---|---:|---:|---:|
| L1 | 31,576 → 27,764 (-12.1%) | 41,911 → 38,112 | 2,069,420 → 1,879,412 |
| L2 | 53,054 → 44,701 (-15.7%) | 69,812 → 60,381 | 3,426,144 → 2,961,084 |
| L3 | 70,248 → 59,214 (-15.7%) | 92,375 → 80,042 | 4,522,240 → 3,913,416 |

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

기존 v001/v002 GLB·편집 blend·통합 맵·검토 폴더·고정 샘플 등 보호 입력 204개 파일의 SHA-256이 그대로다. 새 검수 맵은 기존 맵을 읽어 **건물 인스턴스의 자산 참조만 교체**했다. 지형·길·물·나무·공용 소품의 평가된 정점·면·노멀·색·재질·배치 지문과 카메라·조명·색 관리가 원본과 같다. 원본 맵과 새 맵을 새 프로세스로 다시 열어 확인했다.

지형 Decimate 시험본, bevel 제거, 새 LOD, 새 모델, 색·조명 보정은 적용하지 않았다. 기존 편집 원본을 다시 저장하지 않았고 Android·runtime_samples·프로젝트 기획 문서는 수정하지 않았다.

## 검증과 외관 확인

- 36개를 빈 장면에 독립 재가져오기했다. 메시 1개·재질 1개·primitive 1개·텍스처 0개, 불투명 색, 유한한 단위 노멀, 퇴화 삼각형 0개를 확인했다.
- 원본 외곽·지면 기준·피벗·축·스케일 1을 유지했다. L1/L2/L3 공통 최대 외곽은 원본과 같고 14필지 91쌍의 겹침이 없다.
- 14필지 × 3단계 = 42개 주 출입 경로를 실제 최적화 삼각형으로 다시 검사했다. 폭 0.6m, 높이 0.3/0.85/1.5m 광선에서 충돌이 없었다. 엔진 NavMesh나 모든 보조 출입문의 내부 이동 검사는 아니다.
- 실제 납품 GLB를 사용해 시작·중간·최종 전체와 최종 평면의 전후 4쌍, 12종 각각의 L1~L3 정면·후면·측면 36쌍을 새로 렌더했다. 전후 카메라·조명·색 관리·해상도·64 samples·동일 seed를 맞췄다. 전체는 2400×1500, 단품 행은 3000×1600이다. 기존 PNG가 있다는 이유로 렌더를 생략하지 않았다.
- 40개 전후 비교판과 아치·창틀·힙 지붕 모서리·온실·물레바퀴·발코니·전망탑·다락 뒷창의 같은 픽셀 영역 9개를 실제로 열어 검수했다. 검수한 시점에서는 새 실루엣·구멍·색·그림자 변화를 찾지 못했다. 원본의 기존 어두운 접합부는 그대로 보존했다.
- PNG 코드값과 역 sRGB 변환을 거친 표시 기준 선형 RGB 차이를 구분해 기록했다. 비교판과 크롭은 원래 PNG 코드 바이트를 재배열하며 색 보정을 하지 않는다. AgX를 되돌린 장면 방사량으로 표현하지 않는다.

최종 전체 사선도에서 평균 PNG 코드 RGB 절대 차이는 0.00002075, 코드 채널 차이가 0.01을 넘는 픽셀은 0.03178%다. 동일 원본의 seed만 바꾼 대조 평균은 0.00123681다. 카페·성당·꽃집·물레방앗간 확대 정면과 최종 전체에서 seed 대조 5개를 남겼다. 작은 Cycles 샘플링·수치 차이가 있으므로 픽셀 완전 동일이라고 주장하지 않는다.

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
