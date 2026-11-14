# 앱 UI용 건물 썸네일 v001

- 작성: 2026-11-11. 앱 오른쪽 패널의 건물 목록·다음 단계 미리보기에 쓰는 **투명 PNG 9장(320×320)**이다.
- 원본: [runtime_samples_v001](../runtime_samples_v001/README.md)의 GLB 9개를 **읽기만** 했다. 원본·다른 버전 폴더는 수정하지 않았다. 입력 GLB의 SHA-256은 [렌더 기록](reports/render_report.json)에 남겼고 manifest 값과 같다.
- 3D 장면의 모델 표시는 계속 실제 GLB가 담당한다. 이 썸네일은 목록 아이콘이며 장면 모델을 대체하지 않는다.

## 렌더 조건

- [render_thumbnails.py](source/render_thumbnails.py): Blender 5.2.3 Cycles(GPU), 96 samples, 노이즈 제거, AgX, exposure 0.35.
- 기존 기준 렌더와 같은 3점 조명(Warm window·Sky fill·Back rim)과 world 색을 쓴다. 카메라는 (7, −11, 8) 방향의 직교 투영이다.
- 정점색 `COLOR_0`을 Principled BSDF 기본색에 연결했다. 재질은 불투명, 금속성 0, 거칠기 0.68로 런타임과 같은 성질이다.
- 건물마다 L3 경계에 맞춘 카메라 하나를 세 단계가 함께 쓴다. 그래서 같은 바닥 위치에서 단계별 크기 변화가 보인다.
- 바닥과 그림자 캐처는 넣지 않았다. 처음 그림자 캐처를 넣어 렌더했더니 목록 크기에서 반투명 회색 사각형처럼 보여 제거했다.

## 앱 연결

`android/app/src/main/assets/thumbnails/runtime_samples_v001/`에 같은 파일명으로 복사했다. 앱은 모델 경로 `models/X.glb`를 `thumbnails/X.png`로 바꿔 찾는다. 모델 세트를 바꾸면 같은 규칙으로 썸네일을 다시 렌더해 넣는다.

```powershell
& "$env:LOCALAPPDATA\Programs\Blender Foundation\blender-5.2.3-windows-x64\blender.exe" -b --factory-startup -P art/ui_thumbnails_v001/source/render_thumbnails.py
```

밝은 배경과 Hyundai Blue 배경에 합성해 테두리 번짐·흰 띠·정점색 손실이 없는지 확인했다. 일반 Android 에뮬레이터의 실제 앱 화면에서도 확인했다. Pleos·실차 화면은 확인하지 않았다.
