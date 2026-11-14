# 루미 — Sol minimal

- 날짜: 2026-11-04 (Asia/Seoul).
- 최신 사용자 지시: 루미 몸을 흰색으로 변경. 후보이며 최종 디자인 확정은 아님.
- 생성/편집: 내장 image_gen, 실제 알파 투명 PNG. 이전 사람형 시안 및 애니메이션 참고 이미지는 사용하지 않음.
- v001: 이번 세션에서 새로 생성한 노란 몸 + 두 눈. `art/raw/rumi/sol_minimal_v001.png`에 원본 보존.
- v002: v001만 참조하여 흰 몸으로 편집. `art/raw/rumi/sol_minimal_v002.png`에 생성 편집 원본 보존.
- 작업 범위: 루미의 raw/source/export/review/palettes 폴더만 사용. 공통 문서·도구 및 타 캐릭터는 수정하지 않음.

## Aseprite 작업

- 실행기: 프로젝트 기존 `tools/art/aseprite.ps1`, Aseprite 1.3.8.1-dev.
- 스크립트: 이 폴더의 `prepare_v002.lua`. 작은 시안 전용이며 외부 설치나 시스템 설정 변경 없음.
- 생성 원본의 미세 색 얼룩과 외곽 알파 잡음을 제거하기 위해 새 원화의 실루엣을 측정해 매끄러운 단색 경계로 재구성한다. 눈은 생성 원본의 위치·크기를 기준으로 두 캡슐로 정리한다. 생성 픽셀을 그대로 복사한 출력은 아니다.
- 원본 캔버스 1254 × 1254, 원점과 여백 유지. 자동 트리밍 없음.
- 색 모드: RGB/RGBA, sRGB. Indexed 변환 없음.
- 실제 레이어: `Body - white FFFFFF`, `Eye left - 292733`, `Eye right - 292733`. 몸은 눈 아래까지 채운 독립 실루엣이며 눈 이동·표정 수정에 재사용 가능.
- 팔레트: `art/palettes/rumi/sol_minimal_v002.gpl`. 몸 `#FFFFFF` / 눈 공통 `#292733`. 소품 없음. 경계는 안티앨리어싱 알파 및 합성 중간색을 사용.
- 눈 좌표(원본 기준, 오른쪽·아래 경계 제외): 왼쪽 `(453,496)–(532,658)`、오른쪽 `(710,470)–(788,659)`.
- 작업 파일: `art/source/rumi/sol_minimal_v002.aseprite`.
- 투명 PNG: `art/export/rumi/sol_minimal_v002.png`.

## 검수 기록

실제 파일 검사: `verify_v002.py` → `verification_v002.json`. 전체 검사 통과.

- Aseprite 파일 헤더: 1프레임, 1254 × 1254, 32비트 RGBA. 파일 재열기 후 실제 레이어 이름 세 개 확인.
- 각 레이어의 보이는 모든 픽셀 RGB가 해당 역할 단색과 일치. 몸은 흰색, 두 눈은 같은 짙은 색.
- PNG: RGBA/sRGB, 캔버스 네 변 투명. 불투명 548,933픽셀, 완전 투명 1,020,511픽셀, 경계 반투명 3,072픽셀. 알파 256단계 유지.
- 재열기한 세 레이어의 합성 결과와 최종 PNG 픽셀 일치.
- 직접 시각 검수: 몸 하나·눈 둘, 소품/입/팔다리 없음. 색 얼룩·외곽 잡음·윤곽선·음영 없음. 밝은/어두운 배경의 256px 캔버스 및 64px 캔버스에서 두 눈 구분 확인.
- 밝은 배경에서는 흰 실루엣의 대비가 자연히 낮아진다. 요청한 기본형에 윤곽선이나 그림자는 추가하지 않음.
- 작은 크기 검수는 비교용 64/256px 캔버스 기준이며, 실제 앱 화면 연동 검사는 수행하지 않음.

## v001 생성 프롬프트

```text
Use case: stylized-concept
Asset type: a single original mascot sprite for the audio deduction game Liar Ride, character Rumi.
Create a brand-new extremely minimal mascot on a genuinely alpha-transparent background. No reference images.
Subject: ONE soft round body shape with exactly TWO dark eye shapes. Head and body are one single uninterrupted shape. A warm sunny yellow almost-round oval, subtly taller than wide. Two simple solid dark vertical capsule/oval eyes, with open spacing and a very subtle difference in height suggesting quiet curiosity. Eyes contain no pupils, irises, whites, glints or highlights. The personality must come only from body proportions and eye position, length and spacing.
Style: radically simple flat geometric 2D design, smooth clean antialiased edges. Exactly one flat yellow body color (direction #F6C844) and one flat charcoal eye color (direction #292733). All opaque interiors are perfectly uniform in color.
Composition: square canvas, front view, a single centered mascot occupying roughly 64 percent of the canvas width and 68 percent of the canvas height. Entire silhouette visible with generous transparent margins on all sides.
Use only the body shape and two eye shapes. No accessory in this candidate.
Avoid: human anatomy, humanoid or anime styling, separate head, hair, skin features, clothing, arms, legs, feet, hands, mouth, eyebrows, eyelashes, outline, contour stroke, gradients, shading, shadow, floor shadow, ambient occlusion, gloss, texture, grain, decoration, symbols, text, logos, watermark, border, panels, additional characters.
Do not imitate any specific existing brand mascot or logo. Deliver one finished transparent-background PNG asset, not a sheet or mockup.
```

## v002 흰색 편집 프롬프트

```text
Use case: precise-object-edit.
Edit target: the attached Rumi mascot PNG.
Change ONLY the yellow body fill to a perfectly uniform flat pure white #FFFFFF. Keep the same entire rounded single-body silhouette, proportions, size, placement, canvas, two dark capsule eyes, their positions and their relative lengths. Preserve the same front view and generous transparent margins. The eyes must remain solid dark charcoal. No extra features or accessory.
The finished image must contain just ONE flat white body shape and TWO flat dark eye shapes. Smooth clean antialiased edges, completely flat opaque interiors, no mottling, no shading, no gradient, no outline, no gray rim, no gloss, no texture, no shadow, no mouth, no limbs, no text. Real alpha transparent background, not a checkerboard graphic. Clean stray edge pixels without changing the silhouette.
```

