# 태오 — sol_minimal v001

- 제작일: 2026-11-04 (Asia/Seoul)
- 상태: 사용자가 선택·수정할 첫 미니멀 후보. 도형과 팔레트는 최종 확정 전이다.
- 방향: 살짝 납작한 푸른 몸 하나 + 짧고 가는 짙은 눈 둘. 무심하고 졸린 표정. 소품 없음.
- 신규 생성: 내장 `image_gen` 도구의 `transparent_background=true` 사용. 참조 이미지 입력 없음. 이전 사람형 시안과 애니메이션 참고는 사용하지 않았다.
- 후처리: 기존 Aseprite 1.3.8.1-dev, `tools/art/aseprite.ps1` 배치 실행. 설치·시스템 설정 변경 없음.
- 기존 결과는 보존했다. 이 작업의 출력은 태오 소유 폴더 안의 새 `sol_minimal` 파일뿐이다.

## 파일

| 역할 | 경로 |
| --- | --- |
| 생성 원본, 수정하지 않음 | [sol_minimal_neutral_v001.png](../../../raw/taeo/sol_minimal_neutral_v001.png) |
| 편집 작업 파일 | [sol_minimal_neutral_v001.aseprite](../../../source/taeo/sol_minimal_neutral_v001.aseprite) |
| 실제 알파 투명 PNG | [sol_minimal_neutral_v001.png](../../../export/taeo/sol_minimal_neutral_v001.png) |
| 후보 팔레트 | [sol_minimal_v001.gpl](../../../palettes/taeo/sol_minimal_v001.gpl) |
| 밝은 배경 미리보기 | [preview](sol_minimal_neutral_v001_preview.png) |
| 밝고 어두운 배경 및 축소 검수 | [background_check](sol_minimal_neutral_v001_background_check.png) |
| 실제 Body 레이어 픽셀 | [body](sol_minimal_neutral_v001_body.png) |
| 실제 Eyes 레이어 픽셀 | [eyes](sol_minimal_neutral_v001_eyes.png) |
| Aseprite 정리·출력 스크립트 | [prepare_v001.lua](prepare_v001.lua) |
| 저장·재열기 검수 로그 | [aseprite_v001_checks.txt](aseprite_v001_checks.txt) |
| 독립 파일·픽셀 검사 | [verify_v001.py](verify_v001.py), [verification_v001.json](verification_v001.json) |
| 동일 프롬프트 별도 보관 | [prompt_v001.txt](prompt_v001.txt) |

생성 도구 원본 위치:
`C:\Users\hy\.codex\generated_images\01a1a54b-a09b-7c63-9092-5f555bc722d8\exec-91b560d3-d3e4-46cd-b783-3e90213485df.png`
프로젝트의 raw 파일은 이 원본의 복사본이다.

## 사용한 색과 도형

| 역할 | 후보 HEX | 기록 |
| --- | --- | --- |
| Body | `#5B86AF` | 보이는 Body 레이어의 모든 픽셀 RGB가 이 값과 일치 |
| Eyes | `#172D42` | 보이는 Eyes 레이어의 모든 픽셀 RGB가 이 값과 일치 |

- 캔버스: 원본과 같은 1254×1254. 작업·출력 모두 RGB/RGBA 32비트, 1프레임.
- 몸 바운드: x 255–997, y 358–894, 743×537. 약 1.38:1 비율.
- 사방 여백: 좌 255 / 위 358 / 우 256 / 아래 359픽셀.
- 눈 바운드, 알파 128 이상 기준: 왼쪽 x 457–563 / 오른쪽 x 693–799, 두 눈 모두 y 545–568. 각각 107×24픽셀.
- 머리와 몸 구분, 팔다리, 입, 눈썹, 홍채, 별도 흰 눈알, 소품, 윤곽선 없음.
- 두 기본색 외의 출력 경계 중간색은 눈과 몸의 안티앨리어싱 합성에 따른 값이다. 새로운 명암색을 추가하지 않았다.

## Aseprite 처리

1. 생성 원본의 몸 실루엣과 눈 위치·외곽을 사용했다. 새 도형으로 대체하지 않았다.
2. 몸의 알파 128 이상 행별 범위 주변만 보존해 멀리 떨어진 거의 투명한 잡픽셀을 제거했다.
3. 몸은 후보색으로 채우고, 생성 원본에서 240 이상이던 내부 알파를 255로 정리했다. 외곽의 부분 알파는 유지·정규화했다.
4. 눈은 생성 원본의 두 어두운 도형을 마스크로 추출하고 후보색으로 정리했다. 눈 경계의 중간색을 알파로 풀어 몸 위에 합성했다.
5. 몸 아래쪽의 약간 치우친 배치를 전체 정수 이동 `(+1,-41)`로 중앙 정렬했다. 납품 캔버스의 크기 변경·리샘플링·트리밍 없음.
6. 실제 `Body` / `Eyes` 두 래스터 레이어로 저장했다. `Body`는 눈 뒤에도 이어지는 독립 몸 실루엣이고, `Eyes`에는 두 눈만 있다.
7. 원본에는 색 프로파일이 없어 sRGB를 지정했다. 색 공간 변환은 하지 않았다. PNG에 sRGB 메타데이터가 기록됐다.
8. Indexed 변환·디더링 없음. 미리보기와 검수 시트에만 축소·배경 합성을 적용했다.

생성 원본과 최종 PNG는 단색 정리·알파 정리·중앙 정렬 때문에 픽셀이 다르다. 원본과 최종본이 같다고 주장하지 않는다.

## 검수 결과

| 항목 | 결과 |
| --- | --- |
| 시각 검수 | 몸 하나와 가는 캡슐 눈 둘, 소품 없음. 단색 내부 확인 |
| 실제 투명도 | 네 모서리 알파 0, 전체 완전 투명 픽셀 1,256,291개 |
| 불투명 내부 | 최종 알파 255 픽셀 312,004개 |
| 부드러운 경계 | Body 부분 알파 픽셀 4,221개, 밝고 어두운 배경에서 눈에 띄는 흰 띠·푸른 잔여 흔적 없음 |
| 작은 크기 | 64×64 / 128×128 캔버스 미리보기에서 실루엣과 두 눈 확인. 실제 앱 표시 크기는 아직 확정 전 |
| 실제 레이어 | Aseprite 파일 청크에서도 `Body`, `Eyes` 두 레이어 확인 |
| 눈 마스크 | 알파 128 이상 연결 성분이 정확히 2개 |
| 저장 보존 | 정리한 합성 이미지 = .aseprite 재열기 합성 = PNG 출력, 전체 RGBA 동일 |
| 독립 재합성 | Pillow로 Body/Eyes 재합성 시 Aseprite PNG 대비 채널 최대 차이 1, 합성 반올림 차이 |
| 크기·색 모드 | 원본/레이어/출력 1254×1254 RGBA, Aseprite 32비트, 1프레임 |
| 색 | 각 레이어의 보이는 픽셀 RGB가 역할별 후보색과 정확히 일치 |

검수는 로컬 파일·픽셀 검사와 출력 이미지 직접 확인 기준이다. 앱 연결·실제 게임 화면 검증은 이번 시안 작업에 포함되지 않는다.

## 최종 생성 프롬프트

아래는 내장 이미지 생성 도구에 실제 전달한 전체 프롬프트다.

```text
Use case: stylized-concept.
Asset type: transparent PNG game mascot concept for Liar Ride, one character named Taeo.
Create one original EXTREMELY SIMPLE two-color mascot, consisting of EXACTLY THREE visible shapes: ONE slightly flattened round blue body and TWO short thin dark horizontal capsule eyes. There is no division between head and body. The whole body is one clean smoothly rounded oval / softened pebble silhouette, wider than tall, approximately 1.3 : 1 width to height. Calm muted blue body, first candidate near #5B86AF. Two identical short very thin rounded slit eyes in near #172D42, each roughly 10% of the body width and 2.5% of its height. Place the two eyes at the same height a little above the middle of the body, with a clear modest gap. The eyes alone convey sleepy, quiet indifference. They are solid single-color dark capsules, no white eyeballs, no iris, no pupils nested inside them.
Flat vector-like raster art with perfectly uniform solid color interiors and clean smooth antialiased boundaries. Front view; centered, whole silhouette visible with ample equal transparent margins on a square canvas, body occupying about 62% of the canvas width. Genuine alpha transparent background.
No accessory. No hair, separate head, skin, human anatomy, neck, limbs, hands, feet, tail, ears, mouth, eyebrows, lashes, clothing, ornament, text, logo, watermark, outline, rim, gradient, shadow, lighting, gloss, highlights, texture, background scene, ground, checkerboard pattern, or extra mark. Do not imitate or copy an existing branded avatar; use only the abstract principle of one body and two eyes. This is a tiny minimal geometric mascot, not a humanoid or anime character. Only one character in this image.
```

