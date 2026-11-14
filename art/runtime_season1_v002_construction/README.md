# v004 환경의 건설별 길 표시 파생본

2026-11-11. 승인된 v004의 지형·물·나무·길을 그대로 사용하고 길의 표시 단위만 분리했다. 건물 36개와 원본 blend는 변경하지 않았다. v005 강둑 돌·풀은 포함하지 않는다.

- 원본: `../town_season1_v004_roof_tones/blend/roof_tones_review.blend`의 `AFTER roof tones • final`.
- 출력: [town_environment.glb](exports/town_environment.glb). Android 복사본: `android/app/src/main/assets/models/season1_construction_v001/`.
- [생성 소스](source/export_environment.py)는 별도 장면의 평가된 메시 사본만 가공하며 원본을 저장하지 않는다.
- [길 소유·연결 보고서](reports/environment.json): 기존 L3 진입로의 중심선과 접속 지점을 따라 남쪽 입구에서 각 건물까지의 연결을 추적한다. 다른 진입로와 만나는 곳에서 표시 단위를 나눠 문 앞 전용 구간과 공용 구간을 구별했다. 광장과 성당 앞 계단도 인접 건물에 연결했다. 어느 소유 건물 하나라도 건설됐으면 그 그룹이 보인다.
- 초기 집은 28개 길 그룹 중 자기 진입로와 남쪽 공용 구간 두 개만 표시한다. 꽃가게는 책방의 공용 구간, 방앗간은 빵집의 공용 구간, 농가는 서쪽 집과 식료품점의 공용 구간을 사용한다. 해당 건물이 미건설이면 그 건물의 문 앞 전용 구간은 숨긴다.
- 환경 37,787 triangles 유지. 재가져오기 좌표 오차 최대 0.1mm. [별도 검사](source/verify.py)는 실제 구·신 GLB의 모든 삼각형 위치·노멀·UV·색과 재질 정의를 소수점 네 자리로 비교했다. 완성 상태의 외형은 같다. 건물 36개 SHA-256, 배치·비용·카메라 보존과 두 APK의 자산 바이트도 검사했다. [검사 결과](reports/verification.json).
- 환경 메시 수는 기존 재질별 8개에서 **34개(상시 환경 6 + 길 28)**로 늘었다. 삼각형 수는 같지만 표시 제어에 따른 draw 비용은 늘 수 있다. 이 자료는 Pleos·차량 FPS, 메모리, 발열 검증이 아니다.

Blender 실행:

```powershell
& 'C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe' --background --python art/runtime_season1_v002_construction/source/export_environment.py
python art/runtime_season1_v002_construction/source/verify.py
```

전체 앱 구현·재현·실제 화면은 비공개 개발 문서의 건설 연출 기록을 따른다. 기존 v001 생성 스크립트는 이 파생본을 생성하지 않는다.
