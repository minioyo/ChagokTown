# 차곡마을 — 채택 v004의 Android 런타임 묶음

2026-11-11. 사용자가 강둑 돌·풀 v005를 채택하지 않고 기존 완성본을 프로젝트에 옮기도록 요청한 결과다.

- 기준: [v004 manifest](../town_season1_v004_roof_tones/reports/manifest.json)의 최종 `path`. 건물 12종 × L1~L3 **36개 GLB를 바이트 그대로 복사**했다. 내부 면 제거와 은은한 지붕 톤을 유지한다.
- 환경: `roof_tones_review.blend`의 `AFTER roof tones • final`에서 지형·강·길·계단·나무만 내보냈다. 기존 재질별 평가 메시 사본을 합쳐 **8 meshes / 8 materials / 37,787 triangles**로 묶었다. 정점·지형 높이·강 폭·나무 위치를 편집하지 않았다. 독립 재가져오기에서 0.1mm 단위로 비교한 월드 삼각형 좌표가 같았다. 건물·카메라·조명·v005 소품은 포함하지 않는다.
- [배치](layout.json): 승인된 14부지를 그대로 사용한다. Blender `(x,y,z)`는 Android/glTF `(x,z,-y)`, Z 회전은 Y 회전에 대응한다. 앱의 기존 저장 ID `home`은 미술 부지 `home_entry`에 연결한다. `cafe`·`cathedral`과 모든 기존 단계·잔액은 유지한다.
- [썸네일](thumbnails/): 실제 납품 GLB로 렌더한 투명 320×320 PNG 36개. 이전 패널 디자인과 파일명 규칙을 유지하고 건물별 세 단계에 같은 카메라를 사용한다. 전체 3D 장면은 계속 실제 GLB로 그린다.
- 앱 자산 74개(건물 36·환경 1·썸네일 36·배치 1)는 **11,596,816 bytes**다. 이전 9개 샘플의 원본은 `art/runtime_samples_v001/`에 보존하고 앱 안의 중복 샘플만 제외했다.

## 산출물과 확인

- [원본 대응·SHA-256](reports/manifest.json), [환경 내보내기](reports/environment.json), [썸네일 입력 해시](reports/render_report.json)
- [앱 복사 파일별 해시](reports/published.json), [원본 보존·배치·실제 APK 검사](reports/verification.json)
- 앱 연결·시험 기록과 실제 L3 앱 화면은 비공개 개발 문서에 정리했다.

| 14부지의 단계 | 건물 삼각형 | 환경 포함 삼각형 |
| --- | ---: | ---: |
| 모두 L1 | 27,764 | 65,551 |
| 모두 L2 | 44,701 | 82,488 |
| 모두 L3 | 59,214 | 97,001 |

빈 부지 선택 표시 등 앱에서 생성하는 작은 기하와 그림자 추가 패스는 이 GLB 삼각형 집계에 포함하지 않는다. 실제 GPU 성능·draw call·실차 발열을 측정한 수치가 아니다.

## 재현

프로젝트 루트에서 새 묶음의 스크립트만 실행한다. 이전 버전의 생성 스크립트나 `.blend`는 덮어쓰지 않는다.

```powershell
$blender = 'C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
& $blender -b --factory-startup --python-exit-code 1 -P art/runtime_season1_v001/source/export_environment.py
& $blender -b --factory-startup --python-exit-code 1 -P art/runtime_season1_v001/source/prepare.py
& $blender -b --factory-startup --python-exit-code 1 -P art/runtime_season1_v001/source/render_thumbnails.py
python art/runtime_season1_v001/source/publish.py
# demo/vehicle APK 빌드 후:
python art/runtime_season1_v001/source/verify_delivery.py
```

`publish.py`가 Android 자산을 갱신한다. 새 모델 버전은 원본 manifest와 입력 검사를 함께 갱신해야 한다. 모든 기존 제작 버전은 보존한다.
