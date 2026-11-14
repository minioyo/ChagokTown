# 태오 — 첫 원화 시안

- 제작일: 2026-11-04 (Asia/Seoul)
- 상태: 사용자가 외형을 선택하기 전의 **첫 시안**. 기준 원화·프로젝트 공통 팔레트는 확정하지 않았다.
- 결과: `taeo_neutral_v002`. v001의 표정·머리·의상을 참조해 긴 신체 비율을 줄인 수정본이다.
- 작업 범위: 태오 전용 raw/source/export/review/palettes 폴더. 공통 문서와 실행 스크립트는 변경하지 않았다.

## 결과 파일

| 용도 | 파일 |
| --- | --- |
| 첫 생성 원본, 긴 비율로 미채택 | [taeo_neutral_v001.png](../../raw/taeo/taeo_neutral_v001.png) |
| 수정 생성 원본, 보존 | [taeo_neutral_v002.png](../../raw/taeo/taeo_neutral_v002.png) |
| Aseprite 작업 파일 | [taeo_neutral_v002.aseprite](../../source/taeo/taeo_neutral_v002.aseprite) |
| 투명 PNG | [taeo_neutral_v002.png](../../export/taeo/taeo_neutral_v002.png) |
| 밝은 배경 미리보기 | [taeo_neutral_v002_preview.png](taeo_neutral_v002_preview.png) |
| 밝은/어두운 배경 및 축소 검수 | [taeo_neutral_v002_background_check.png](taeo_neutral_v002_background_check.png) |
| 수치 검증 결과 | [verification_v002.json](verification_v002.json) |
| 이 시안의 픽셀 색상 표본 | [concept_v002_samples.md](../../palettes/taeo/concept_v002_samples.md) |

Aseprite 파일은 RGB 모드, 32비트 RGBA, 1프레임, **원화를 담은 단일 래스터 레이어**다. 선·피부·옷이 자동 분리된 작업 파일은 아니다. 미리보기의 크림색/먹색은 검수용 합성 배경이며 투명 PNG에는 추가하지 않았다.

## 사용 도구와 처리

1. 프로젝트 `AGENTS.md`, `docs/ART_GUIDE.md`, `docs/IDEA.md` 및 imagegen 스킬을 읽었다.
2. 내장 `image_gen.imagegen`으로 v001을 생성했다. `transparent_background=true`; 참조 이미지 없음.
3. v001을 직접 확인하고, 비율이 약 3등신 방향보다 길어 v001을 참조한 내장 이미지 편집으로 v002를 생성했다. `transparent_background=true`.
4. 생성 파일을 아래 위치에서 태오 raw 폴더로 복사했다. 생성 원본은 덮어쓰지 않았다.
   - v001: `C:\Users\hy\.codex\generated_images\01a1a52f-c5f6-7a82-8c1a-ec3d965cc542\exec-db04f8af-19e4-41ec-becf-a5cbfba9cb41.png`
   - v002: `C:\Users\hy\.codex\generated_images\01a1a52f-c5f6-7a82-8c1a-ec3d965cc542\exec-2b20545a-6da0-4bf2-904e-2c176305df27.png`
5. 기존 Aseprite **1.3.8.1-dev**와 프로젝트 `tools/art/aseprite.ps1`을 통해 [prepare.lua](prepare.lua)를 배치 실행했다.
6. 프로파일이 없는 생성 PNG에 **sRGB를 지정**했다. 다른 색 공간으로부터 RGB 값을 변환한 것이 아니다. 팔레트 매핑, Indexed 변환, 색상 양자화, 자동 트리밍은 하지 않았다.
7. `.aseprite` 저장 후 재열고 PNG를 내보냈다. 별도의 검수 이미지에만 bilinear 축소 및 배경 합성을 했다.
8. Python/Pillow는 PNG 메타데이터·픽셀·파일 해시의 읽기 및 JSON 검증 보고서 기록에만 사용했다. 원화 수정·색상 보정·축소·합성은 Python으로 수행하지 않았다.
9. 별도 이미지 API 호출이나 새 소프트웨어 설치는 하지 않았다.

실행 명령:

```powershell
pwsh -NoProfile -File tools\art\aseprite.ps1 --script art/review/taeo/prepare.lua
python art\review\taeo\verify.py
```

`prepare.lua`는 기존 납품 파일의 덮어쓰기를 거부한다. 후속 시안은 파일명과 경로를 새 버전으로 바꾼 뒤 실행한다.

API 확인: [Aseprite Sprite API](https://www.aseprite.org/api/sprite)에서 RGB 색 공간 지정과 저장/재열기 동작, [Aseprite Image API](https://www.aseprite.org/api/image)에서 검수용 합성·bilinear 축소를 확인했다.

## 검수 결과

| 항목 | 결과 |
| --- | --- |
| 콘셉트 | 남색 후드, 목의 헤드폰, 반쯤 감긴 눈, 살짝 옆을 보는 시선, 편안한 주머니 자세 확인. |
| 구조 | 헤드폰은 두 이어컵과 연결된 밴드로 구성. 손은 주머니 안에 있어 손가락 노출 없음. 소매·주머니 입구·발 구조에 중대한 오류를 발견하지 못했다. 안경·가방·끈 소품 추가 없음. |
| 전신·여백 | 머리와 양쪽 신발이 잘리지 않음. 알파 128 이상 실루엣 범위는 x=226..782, y=232..1452. 캔버스 여백은 좌 226 / 우 241 / 상 232 / 하 83px. |
| 투명도 | 실제 RGBA. 네 모서리 알파 0. 완전 투명 픽셀 1,138,867개. 밝고 어두운 합성 배경에서 눈에 띄는 흰 띠·번짐·바닥 그림자 없음. |
| 알파의 한계 | 생성 원본의 알파는 0..254이며 인물 내부는 주로 253/254다. 완전 불투명 255 픽셀은 없다. 실루엣 밖에 알파 1..7의 극미세 잔여값이 있다. 첫 시안의 반투명 테두리를 보존하기 위해 임계값 처리하지 않았으며 앱 최종 납품용 마스크 정리는 별도 단계다. |
| RGBA 보존 | 원본 v002 대비 출력의 **전체 RGBA 바이트 일치**, 알파 변경 0, 보이는 픽셀 변경 0, 완전 투명 픽셀의 숨은 RGB 변경 0. |
| 작업 파일 | 재열기 성공. Aseprite 헤더에서 1024×1536, 32비트, 1프레임을 별도 확인. |
| PNG | 1024×1536 RGBA, sRGB 메타데이터 확인. PNG 파일 바이트 해시는 메타데이터·압축 차이로 원본과 다르지만 디코딩한 픽셀은 동일. |
| 축소 | 캔버스 높이 768 / 192 / 128px의 밝고 어두운 검수본을 직접 확인. 192px에서는 눈매·입·헤드폰이 구분됨. 128px에서는 얼굴의 미세한 뉘앙스가 약해지지만 인물 실루엣·졸린 눈매·헤드폰은 읽힘. 실제 앱 크기는 미정이므로 앱 화면 테스트는 하지 않았다. |
| 공통 스타일 | 2D 펜선, 큰 색면과 단순한 그림자, 짧은 캐릭터 비율 유지. 픽셀아트·3D 광택·글자·장식 테두리·유령 정답 효과 없음. 생성 이미지의 미세 색상 편차는 남아 있으며 단색 HEX 보정을 완료했다고 주장하지 않는다. |

세 캐릭터의 최종 기준 원화가 아직 선택되지 않았으므로, 최종적인 선 굵기·신체 비율·색상 통일은 선택 이후 검토한다. 이 시안은 독립적인 태오 후보이며 다른 세션의 결과를 덮어쓰지 않는다.

## v001 생성 프롬프트

```text
Use case: stylized-concept
Asset type: first character concept illustration for the original 2D indie deduction game Liar Ride.
Create ONE finished original character, Taeo, as a standalone raster PNG asset, portrait 1024 x 1536 composition if possible.

BACKGROUND: genuinely transparent alpha background. No scenery, floor, ground shadow, checkerboard artwork, border, text, labels, logo, or watermark.

SUBJECT AND PERSONALITY: Taeo is an aloof, sleepy-looking but very observant traveler. A navy-blue hoodie, hood lowered behind the neck; a single well-constructed pair of over-ear headphones resting around his neck; half-lidded eyes with clearly visible pupils, a quiet sideways attentive glance, subtly asymmetric eyebrows, and a small neutral mouth. Sleepy, low energy, dry and understated, but alive and perceptive rather than vacant, depressed, or doll-like. Softly tousled dark charcoal hair. Relaxed shoulders with slight asymmetry, easy weight resting on one leg, hands naturally tucked into the hoodie's single kangaroo pocket. Simple muted gray trousers and uncomplicated off-white sneakers. Keep clothing and headphones physically coherent and readable; two earcups connected by one headband.

STYLE: cute with a slightly suspicious personality, hand-drawn 2D indie mystery-game illustration. Approximately three head-heights tall, distinct readable face and hoodie-led silhouette. Dark near-black ink contours with gentle natural line-weight variation; large flat matte color areas; one simple cel-shadow step. Smooth 2D raster illustration, NOT pixel art. Clean expressive economical shapes and very few interior details. Strong eye and mouth legibility when reduced to a small game character. No 3D gloss, gradients, dramatic lighting, paper grain, distressed texture, noise or decorative hatch marks.

COMPOSITION: near-front view, one whole figure centered in a vertical 2:3 canvas. Show every bit of hair, hoodie, headphone and both shoes, leaving generous clear transparent padding on all four sides. No cut-off body or props. Natural slight posture asymmetry without a dramatic pose.

COLORS: ink-dark outline, muted deep navy hoodie with a darker navy shadow, warm natural skin, charcoal hair, subdued headphone and trouser grays, off-white shoes. These are a preliminary concept's color relationships, not a finalized project palette.

CONSTRAINTS: exactly one character and one illustration. Do not add bags, hats, glasses, maps, extra objects, supernatural cues, ghost glow, transparency within the character, or any visual hint revealing a ghost role.
```

## v002 최종 편집 프롬프트

입력 이미지: `art/raw/taeo/taeo_neutral_v001.png` (수정 대상 및 정체성 참조)

```text
Use case: identity-preserve
Image 1 is the edit target and identity reference: Taeo's preliminary illustration.
Revise this into the requested compact THREE-HEAD-TALL cute 2D indie mystery-game character. This is a necessary proportion correction, not a new character.

CRITICAL PROPORTIONS: the entire figure from hair crown to shoe soles must be approximately THREE times the height of his head from hair crown to chin. A large expressive head taking one third of the full character height, compact short hoodie torso taking another third, short legs and shoes taking the last third. Strongly shorten the reference's long torso and long legs. Do not keep adult or five-head-tall proportions. Retain his sleepy observant face and dark tousled hairstyle, simplified for the small silhouette.

KEEP: navy hoodie with lowered hood, a single connected pair of gray over-ear headphones resting around the neck, half-lidded attentive eyes looking slightly sideways, simple neutral mouth, laid-back asymmetric shoulders, hands tucked in the single kangaroo pocket, muted gray pants, off-white sneakers. Preserve the understated personality, visible pupils and living expression. No new props.

STYLE: dark ink contours, gently varying pen weight, smooth NON-PIXEL 2D illustration, large truly flat matte color fills with only ONE discrete darker shadow tone per material. Remove gradient-like lighting and unnecessary folds or sneaker details. Cute, mildly suspicious, calm; not lifeless.

CANVAS AND ALPHA: portrait 1024 x 1536 if possible. Near-front full body centered. Fit the COMPLETE character inside the central 78 percent of the canvas height, with at least 140 pixels of clear empty space above the hair and below the shoes on a 1536px canvas. Generous empty sides too. The figure itself is fully opaque. Background is genuine alpha=0 transparency, including between the legs. REMOVE ALL the reference's smoky gray halo, glow, vignette and ground haze; outside the character silhouette there must be NOTHING at all, no shadow. Only the thin anti-aliased contour may be semi-transparent. Do not paint a black or checkerboard background.

No scene, floor, floor shadow, atmospheric glow, text, frame, watermark, supernatural cue, added bag, hat, glasses, or map. Deliver one character concept only.
```

