# 모카 — sol_minimal v001

- 제작일: 2026-11-04
- 상태: 사용자 선택 전 첫 후보. 도형·비율·HEX는 최종 확정값이 아니다.
- 방향: 자기 추리에 자신 있는 모카. 둥근 사각형 몸 하나와 안쪽으로 살짝 기울어진 캡슐 눈 둘. 소품 없음.
- 생성: 내장 `image_gen`, `transparent_background=true`. 참조 이미지 없음. 이전 사람형·애니메이션풍 이미지와 브랜드 로고를 입력으로 사용하지 않았다.
- 후처리: 프로젝트의 `tools/art/aseprite.ps1`로 기존 Aseprite를 배치 실행. 새 설치나 시스템 설정 변경 없음.
- 다른 캐릭터 및 공통 문서·도구는 수정하지 않았다. 기존 모카 결과도 보존했다.

## 결과 파일

| 용도 | 파일 |
| --- | --- |
| 생성 원본, 바이트 그대로 보관 | [sol_minimal_neutral_v001.png](../../../raw/moka/sol_minimal_neutral_v001.png) |
| 편집 가능한 작업 파일 | [sol_minimal_neutral_v001.aseprite](../../../source/moka/sol_minimal_neutral_v001.aseprite) |
| 투명 PNG | [sol_minimal_neutral_v001.png](../../../export/moka/sol_minimal_neutral_v001.png) |
| 후보 팔레트 | [sol_minimal_v001.gpl](../../../palettes/moka/sol_minimal_v001.gpl) |
| 밝은/어두운 배경 비교 | [review_v001.png](review_v001.png) |
| 구조 검수 | [structure_v001.json](structure_v001.json) |
| 픽셀·알파 검수 | [verification_v001.json](verification_v001.json) |

작업 파일은 1254 × 1254, 32비트 RGB/RGBA, sRGB, 한 프레임이다. 실제 레이어는 아래 두 개이며, 몸은 눈 아래까지 온전히 채워져 있어 표정 변형에 재사용할 수 있다.

| 레이어 | 내용 | 기준색 |
| --- | --- | --- |
| `Body` | 둥근 사각형 하나 | `#D97565` / RGB 217, 117, 101 |
| `Eyes` | 캡슐 눈 둘 | `#312629` / RGB 49, 38, 41 |

## Aseprite 정리 내용

생성 원본에는 미세한 RGB 얼룩, 거의 불투명한 내부 알파(주로 254), 본체 밖의 희미한 잔여 픽셀이 있었다. 단순한 색면을 얻기 위해 생성 결과의 실측 위치와 비율에 맞춰 Aseprite Lua에서 둥근 사각형과 두 캡슐의 경계를 정규화하고 두 기준색으로 채웠다. 생성 원본의 모든 경계 픽셀을 그대로 유지한 출력은 아니다.

- 캔버스 크기와 배치는 유지하고 자동 트리밍하지 않았다.
- 몸의 가시 범위: x=221..1020, y=313..982. 폭 800, 높이 670, 모서리 반지름 210 px.
- 눈 범위: 왼쪽 약 x=450..523, 오른쪽 약 x=730..803, y=519..655. 안쪽으로 약 11.8도 기울어진 캡슐.
- 전체 캐릭터는 캔버스 안에 있으며 여백은 왼쪽 221, 오른쪽 233, 위 313, 아래 271 px이다.
- 내부는 불투명 단색이며 도형 경계에만 부드러운 안티앨리어싱을 적용했다.
- 몸과 눈을 실제로 분리했다. 확인용 [몸 PNG](sol_minimal_neutral_v001_body.png), [눈 PNG](sol_minimal_neutral_v001_eyes.png)도 저장했다.
- RGB 모드를 유지했고 Indexed 변환을 적용하지 않았다.

실행한 모카 전용 후처리:

```powershell
pwsh -NoProfile -File tools/art/aseprite.ps1 --script art/review/moka/sol_minimal/prepare_v001.lua
```

재실행 시 기존 작업 파일과 최종 PNG를 덮어쓰지 않도록 중단한다. 변경안은 새 버전으로 만든다.

## 검수 결과

- 직접 확인: 몸 하나와 눈 둘만 있고 머리 분리, 팔다리, 입, 머리카락, 의상, 소품, 윤곽선, 그림자, 질감이 없다.
- Aseprite 저장본을 재열어 RGB 모드, 크기, 한 프레임, `Body`·`Eyes` 레이어 이름과 표시 상태를 확인했다.
- 저장된 Aseprite 바이너리 헤더의 32비트 깊이와 sRGB 프로파일 유형 1을 확인했다. PNG에도 sRGB 청크가 있다.
- PNG는 실제 RGBA이다. 완전 투명 픽셀 1,073,752개, 바깥 경계의 반투명 픽셀 1,324개, 불투명 픽셀 497,440개를 확인했다.
- 분리된 각 레이어의 모든 가시 픽셀 RGB가 해당 기준색과 정확히 일치한다. 합성 PNG의 눈/몸 경계에는 안티앨리어싱 혼합색이 있으므로 PNG 전체의 RGB 종류가 두 개뿐이라는 의미는 아니다.
- [재열기 출력](sol_minimal_neutral_v001_roundtrip.png)의 RGBA 픽셀이 최종 PNG와 완전히 일치한다.
- 생성 원본의 프로젝트 사본이 원래 생성 파일과 바이트 단위로 일치한다.
- [비교 미리보기](review_v001.png)는 왼쪽이 밝은 배경 `#F4F0E8`, 오른쪽이 어두운 배경 `#242830`이며, 각 배경에서 왼쪽부터 256·128·64 px 캔버스이다. 직접 열어 외곽의 흰 띠·잔여 픽셀이 없고 작은 크기에서도 눈 둘이 구분됨을 확인했다.
- 실제 게임 화면에 연결한 검수는 하지 않았다. 최종 앱 표시 크기와 팔레트 채택은 미정이다.

픽셀 검수 명령:

```text
python -B art/review/moka/sol_minimal/inspect_v001.py
```

이 Python 파일은 픽셀을 읽어 검수하고 JSON 기록을 저장한다. PNG의 색이나 알파를 편집하지 않는다. 이미지 편집과 PNG 출력은 Aseprite에서 수행했다.

## 실제 생성 프롬프트

동일한 텍스트를 [prompt_v001.txt](prompt_v001.txt)에도 보관했다.

```text
Use case: stylized-concept.
Asset type: transparent game mascot concept for Liar Ride, Moka.
Create ONE original extremely minimal mascot on an actual alpha-transparent background. No reference images. Flat smooth 2D shapes, not pixel art.
The ENTIRE visible character consists of exactly THREE shapes: one softly rounded square body and two small dark capsule eyes. No accessory.
The body is a single near-square rounded rectangle, slightly wider than tall, with generous rounded corners. Head and body are the SAME single shape. Use one uniform muted brick-coral fill, target #D97565.
The two eyes use the SAME solid deep warm charcoal fill, target #312629. Each eye is a short slender capsule with rounded ends, subtly tilted inward about 7 degrees. Keep the tilt restrained, with enough space between the eyes to suggest quiet self-confidence in her own deductions. Eyes sit slightly above the center of the body, centered as a pair. Each eye is one filled shape only; no eyeball white, iris, pupil, highlight, lashes or brows.
Front view, no perspective. Square canvas. Center the complete mascot with roughly 20 percent transparent margin on all four sides. Body occupies roughly 60 percent of canvas width and height. All outer edges smooth and clearly antialiased.
Color constraints: exactly one flat body color and one flat eye color, with only edge antialiasing. No outlines, gradients, shading, drop shadows, glow, gloss, reflections, texture, speckles, lighting or 3D rendering.
No arms, legs, hands, feet, ears, hair, nose, mouth, eyebrows, clothing, neck, separate head, facial features beyond the two eyes, symbols, lettering, signature, background objects, ground plane, checkerboard pattern or opaque background.
This is a new original shape mascot, not a copy of any existing avatar, robot or brand logo. Deliver one clean isolated transparent PNG image, not a comparison sheet or presentation.
```

