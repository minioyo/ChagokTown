# 모카 첫 원화 시안 — v002

- 제작일: 2026-11-04 (Asia/Seoul)
- 상태: 사용자 선택 전 첫 시안. 프로젝트 기준 원화·최종 공통 팔레트 확정 아님.
- 사용 지침: 프로젝트 AGENTS.md, docs/ART_GUIDE.md, imagegen 스킬. 사용자 요청에 따라 캐릭터별 독립 시안을 제작했다.
- 수정 범위: art/raw/moka/, art/source/moka/, art/export/moka/, art/review/moka/, art/palettes/moka/만 사용. 공통 문서와 실행 스크립트는 변경하지 않았다.

## 최종 파일

| 역할 | 경로 |
| --- | --- |
| 첫 생성 원본, 보존 | ../../raw/moka/moka_concept_v001.png |
| 참조 편집 원본, 최종 시안의 원본 | ../../raw/moka/moka_concept_v002.png |
| Aseprite 작업 파일 | ../../source/moka/moka_concept_v002.aseprite |
| 실제 투명 PNG | ../../export/moka/moka_concept_v002.png |
| 밝은 배경 검수본 | moka_v002_light_1024.png |
| 어두운 배경 검수본 | moka_v002_dark_1024.png |
| 축소 검수본 | moka_v002_light_256.png, moka_v002_dark_256.png, moka_v002_light_128.png, moka_v002_dark_128.png |
| Aseprite 재열기 후 PNG | moka_v002_roundtrip.png |
| 픽셀·크기·알파·해시 검사 | verification_v002.json |
| 시안 색상 표본 | ../../palettes/moka/moka_concept_v002_samples.json |

작업 파일은 RGB/RGBA, 1프레임, 원화를 담은 단일 래스터 레이어다. 선·피부·의상을 별도 레이어로 분리한 파일은 아니다. 배경 합성본은 검수 전용이며 최종 PNG에는 배경이 없다.

## 제작 및 도구 기록

1. 내장 image_gen 도구로 v001 생성. transparent_background=true. 별도 API, CLI 이미지 생성, 소프트웨어 설치를 사용하지 않았다.
2. v001을 직접 보고 전신이 지나치게 길고 상하 여백이 좁아, 동일 원본을 기준으로 비율과 프레이밍을 참조 편집했다. 원본은 덮어쓰지 않았다.
3. v002 참조 편집에도 내장 image_gen 도구와 transparent_background=true 사용. 참조 경로는 art/raw/moka/moka_concept_v001.png.
4. 생성 결과를 아래 기본 저장 위치에서 모카 전용 raw 폴더로 복사했다.
   - v001: C:/Users/hy/.codex/generated_images/01a1a52f-cd6f-7ea0-a6bd-388b24a8dad8/exec-f21496e9-83bf-4a4b-85a2-d5e41d17ef1c.png
   - v002: C:/Users/hy/.codex/generated_images/01a1a52f-cd6f-7ea0-a6bd-388b24a8dad8/exec-5aefb5da-03db-44b0-a928-65aa72237c93.png
5. 기존 Aseprite 1.3.8.1-dev를 tools/art/aseprite.ps1로 실행했다. export.lua에서 RGB 상태로 작업 파일·PNG를 저장하고 밝은/어두운 배경 검수본을 만들었다.
6. verify.lua로 .aseprite를 다시 열어 PNG로 내보냈다. prepare.py는 원본 복사, 읽기 전용 픽셀 검사, Aseprite 실행 및 검수 JSON 작성에만 사용했다. Python으로 그림을 그리거나 수정하지 않았다.
7. Indexed 변환, 팔레트 매핑, 색상 보정, 자동 트리밍을 하지 않았다. 생성 원본의 모든 RGBA 값을 보존했다.

실행 기록:

```powershell
python -B art/review/moka/prepare.py v002
python -B art/review/moka/prepare.py export
python -B art/review/moka/prepare.py verify
```

Aseprite 호출은 스크립트 내부에서 다음 방식으로 실행된다.

```powershell
pwsh -NoProfile -File tools/art/aseprite.ps1 --script art/review/moka/export.lua
pwsh -NoProfile -File tools/art/aseprite.ps1 --script art/review/moka/verify.lua
```

## 검수 결과

| 항목 | 실제 확인 결과 |
| --- | --- |
| 콘셉트 | 벽돌색 베레모, 동그란 안경, 접힌 여행 지도, 자신 있는 곁눈질과 작은 미소. 단정하게 선 여행자. |
| 비율·구도 | 큰 머리와 짧은 몸의 약 3등신 시안. 모자·지도·신발이 잘리지 않았다. 1024×1536 세로 캔버스 유지. |
| 구조 | 두 안경테와 연결부, 지도 쥔 손과 허리에 댄 손, 소매·손목 연결, 바지·신발을 직접 확인. 눈에 띄는 중복 사지·끊긴 끈 없음. 가방끈은 없는 디자인. |
| 표현 | 짙은 펜선, 큰 색면, 단순한 그림자. 일부 면에는 미세한 색 변화가 남아 있어 정확한 단색 팔레트 일치를 주장하지 않는다. |
| 실제 알파 | RGBA PNG. 완전 투명 픽셀 1,089,100개. 네 모서리 alpha=0. 알파 범위 0–254. |
| 원본 알파 특성 | 캐릭터 내부는 대부분 alpha=253–254이며 외곽에 alpha=1–3인 미세 픽셀이 일부 있다. 원본을 그대로 보존했으며 완전 불투명 255로 강제하지 않았다. |
| 화면상의 번짐 확인 | 생성 도구의 미리보기에는 투명 픽셀 아래 RGB가 검은/갈색 번짐처럼 보였다. 알파 합성을 적용한 밝은 #F4F0E8 / 어두운 #242830 검수본에서는 눈에 띄는 넓은 번짐·흰 테두리를 발견하지 못했다. |
| 실제 캐릭터 범위 | alpha≥16 기준 bbox [196,230,845,1408), 좌/우 여백 196/179px, 상/하 여백 230/128px. 극미량 알파까지 포함한 bbox는 [49,101,994,1410). |
| 작은 크기 | 256×384 캔버스에서 눈썹·곁눈질·입과 베레모·안경·지도 구별 가능. 128×192에서도 캐릭터와 소품은 읽히지만 미세한 표정 구별은 약해진다. 앱 표시 크기는 아직 미정이므로 실제 앱 검수는 미실시. |
| RGBA 보존 | raw v002 → 최종 PNG, raw v002 → Aseprite 재열기 PNG 모두 디코딩한 RGBA 바이트 전체 일치. 캔버스·위치·반투명 경계 유지. |
| 작업 파일 | 헤더와 재열기 검사에서 1024×1536, 32bit RGB/RGBA, 1프레임, 1레이어 확인. |
| 색 공간 | raw PNG에 프로파일 없음. sRGB로 해석하여 저장했고 출력 PNG에 sRGB 태그가 추가됐다. RGBA 값은 그대로이며 다른 프로파일에서 변환한 결과가 아니다. |
| 팔레트 | 시안의 단일 픽셀 HEX 표본만 별도로 기록. 공통 팔레트로 확정하거나 일괄 적용하지 않았다. |
| 게임 조건 | 배경 장면·바닥 그림자·글자·테두리·유령 정답을 암시하는 효과 없음. |
| 남은 선택 | 사용자가 얼굴·의상·비율 방향을 선택할 단계. 다른 두 캐릭터의 최종 그림과 직접 비교한 통일성 검수는 하지 않았다. |

RGBA SHA-256: 66f8d95c3dbd2ad4d7233b6b034203ed65fc1aa54574524d1dc8b708e3161927

## 최종 참조 편집 프롬프트 — v002

참조 이미지: art/raw/moka/moka_concept_v001.png (캐릭터 디자인 기준 및 수정 대상).

```text
Use case: style-transfer
Asset type: corrected first character concept for Liar Ride.
Input image 1: Moka character design reference and edit target.

Preserve this exact Moka identity: the tilted brick-red beret, short cocoa-brown outward curling bob, round dark-rimmed glasses, raised eyebrow and sideways glance, small confident closed smile, brown travel jacket over cream shirt with red neckerchief, olive-brown trousers and dark brown boots, folded map held in one hand, other hand on the hip. Preserve coherent hands, the simple map route marks, the face shape and hairstyle. One character only.

Correct the drawing to the intended game-asset presentation:
- Make a genuinely cute THREE-head-tall chibi character. Keep the expressive head large; substantially shorten the excessively long torso and legs of the reference. Head including hat roughly one third of the full character height. Short, tidy compact legs and boots, upright pose.
- A 1024 x 1536 portrait canvas with the whole character centered and safely inside the canvas. The character from top of beret to bottom of boots occupies only about 78 percent of the canvas height, leaving at least 140 pixels of clear empty margin above and below. Preserve clear space at both sides including around the map.
- True clean RGBA transparency outside the character. Completely remove the smoky brown/black halo around the reference. No background pixels, glow, shadow, aura, vignette, fog, floor, gradient backdrop, or checkerboard painting. All exterior empty space is alpha zero. Character interiors should be fully opaque, with smooth antialiasing only at silhouette edges.
- Clean flat matte cel-shaded 2D illustration: dark ink outlines with gentle pen width variation, large solid color regions, a single simple hard-edged shadow shade per material. Eliminate all soft airbrush gradients and grain from inside the reference. This is smooth hand-drawn cartoon illustration, not pixel art.

Keep the charming self-confident detective-like traveler personality: clever, slightly prickly, cute but a little suspicious. Clear eyes, eyebrows and mouth even in a small game UI. No additional props, no text, no watermark, no frames, no ghost clues, no supernatural symbols.
```

## 최초 생성 프롬프트 — v001

참조 이미지 없음.

```text
Use case: stylized-concept
Asset type: first character concept illustration for the 2D indie deduction game Liar Ride. One finished character illustration only.

Primary request: Draw Moka, an original cute but faintly suspicious traveler who acts like a detective and is very confident in their deductions. Moka wears a brick-red beret and clearly round dark-rimmed glasses, and carries a folded travel map. The face should suggest someone precise, observant, and self-assured who would bristle if their reasoning were challenged: one slightly raised eyebrow, alert sideways-checking eyes, and a small closed-mouth knowing smile. Let the eyes and eyebrows remain clearly visible through the glasses, without lens glare. Tidy upright stance. One hand grips the folded map naturally, the other rests confidently at the hip. Clearly coherent hands, joints and clothing. Short cocoa-brown hair, simple tidy travel clothing with large uncluttered shapes. The beret, glasses and folded map are the distinguishing visual features.

Style/medium: Charming hand-drawn 2D indie mystery-game illustration, approximately three heads tall. Dark ink-black outlines with subtle natural variation in pen width. Large flat matte color areas, just one simple cel-shaded shadow step. Smooth illustrated edges, NOT pixel art. Clear expressive eyes and mouth, strong readable silhouette at small game-UI sizes. Cute, clever, slightly prickly personality, not sinister.

Composition/framing: Portrait canvas, preferably 1024 x 1536 pixels. One full-body character near frontal view, centered, entirely visible from top of beret to bottom of both shoes. Generous empty margin on all four sides, including around the map. No contact with canvas edges. No inset portraits, no duplicates, no multiple views.

Scene/backdrop: Actual alpha-transparent background, clean RGBA cutout. All empty space must be genuinely transparent, not white or a painted checkerboard. No floor, no cast ground shadow.
Color palette: Brick-red beret, dark ink lines, restrained warm natural colors. This is a provisional concept, not an established project palette.
Text: None. The map uses only a few simple graphical route and fold marks, no words or letters.
Avoid: scenery, background scene, ground shadow, text, title, watermark, borders, decorative frames, sparkle, aura, ghost clues, supernatural symbols, transparency on the character body, 3D rendering, glossy material, excessive gradients, paper noise, texture grain, unnecessary accessories, straps with no functional attachment, extra fingers or limbs.
```

