# 차곡마을 (ChagokTown)

평소의 이동이 작은 마을을 키우는 재료가 되고, 주차한 뒤 잠깐씩 그 마을을 가꾸는 **차량용 3D 마을 성장 게임**입니다.
Hyundai Pleos(Android Automotive) 차량 화면을 대상으로 하며, 일반 Android 기기에서 돌려 볼 수 있는 시연(demo) 빌드도 함께 제공합니다.

## 게임 소개

- **14개 부지, 12종 건물, 건물마다 L1→L3 3단계 강화.** 미니어처 디오라마 같은 3D 마을에서 건물을 눌러 고르고, 마을 조각으로 짓거나 키웁니다. 처음에는 작은 집 L1과 마을 조각 3개로 시작합니다.
- **이동 확인 보상.** 주차 후 마을을 열 때 차량의 누적 주행거리를 한 번 읽어 지난번 값과 비교합니다. 1.0km 이상 이동했다면 하루 한 번, 마지막 보상 이후 지난 날짜 1일당 조각 3개(최대 7일치)를 받습니다. 거리·속도·주행 시간에 비례하지 않으므로, 매일 운전하든 주말에만 운전하든 시즌 진행 속도가 비슷합니다.
- **장소 연결(선택).** 지은 건물에 "단골 카페" 같은 별명만 붙이거나, 지금 주차한 곳의 위치를 연결할 수 있습니다. 장소를 연결해도 보상은 늘지 않습니다. 장소는 의미를 남기는 기능일 뿐입니다.
- **주행 중에는 잠금.** 차량이 주행 제한 상태를 알리면 즉시 플레이와 3D 렌더링을 멈춥니다. 제한 전에 승인된 저장만 끝까지 반영합니다.

## 개인정보와 안전 설계

- 차량 정보 사용과 위치 사용은 **각각 따로 동의**받고, 처음에는 꺼져 있습니다. 끄면 관련 기록을 바로 지우며 건물과 받은 조각은 그대로 남습니다.
- 비교에 필요한 마지막 주행거리 하나와 연결한 장소의 별명·좌표만 저장합니다. 경로나 주행 이력은 저장하지 않습니다.
- 저장하는 값은 Android Keystore 키로 **AES-256-GCM 암호화**해 Room에 넣습니다. 레코드·필드별 AAD로 묶어, 봉투를 다른 행에 복사하면 열리지 않습니다.
- 자동 백업·기기 이전에서 앱 데이터를 제외했고, 인터넷 권한을 제거했습니다.
- 동의를 바꾸거나 주행 제한·백그라운드로 전환되면 세대(generation)가 바뀝니다. 그 전에 요청했다가 늦게 도착한 주행거리·위치 응답은 버립니다.

## 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| 언어·UI | Kotlin 2.2, Jetpack Compose (Material 3) |
| 3D | SceneView 2.3 (Filament), glTF(GLB) 모델, 직교 카메라 |
| 저장 | Room 2.8 (schema v5, v1부터 단계별 마이그레이션) |
| 비동기 | Kotlin Coroutines / Flow |
| 차량 연동 | Pleos Vehicle SDK 2.3.2, `CarUxRestrictionsManager`, `LocationManager` |
| 보안 | Android Keystore, AES-256-GCM |
| 빌드 | AGP 8.13, Gradle 8.13, JDK 17, minSdk 28 / targetSdk 36 |
| 아트 | Blender (Python 생성 스크립트) → GLB 내보내기 |

## 프로젝트 구조

```text
android/
  game/              순수 Kotlin 게임 규칙(건설·강화, 이동 보상)과 JVM 단위 테스트
  app/
    src/main/        Compose UI, 3D 장면, ViewModel, Room 저장, 암호화, 세션 게이트
    src/demo/        가상 주행·날짜·주행 제한 버튼이 있는 시연 빌드
    src/vehicle/     Pleos SDK, 주행 제한, 위치 연동
    schemas/         Room 스키마 기록(마이그레이션 검증용)
art/                 건물·마을 3D 원본(.blend), 생성 스크립트, 런타임 GLB
tools/               아트 작업 보조 스크립트
```

주요 설계 원칙:

- **규칙과 플랫폼 분리.** 게임 규칙은 Android 의존성이 없는 `:game` 모듈에 두고 JVM에서 테스트합니다. 차량 읽기는 `VehicleGateway` 인터페이스 뒤에 숨기고, demo와 vehicle flavor가 각자 구현합니다.
- **flavor 격리.** demo APK에는 Pleos SDK와 차량 권한이 없고, vehicle APK에는 시연 버튼과 시연 재료 지급 코드가 없습니다.
- **한 번에 저장하거나, 아예 저장하지 않기.** 쓰기는 하나의 Mutex와 Room 트랜잭션 안에서 처리합니다. 보상·기준 주행거리·보상 날짜도 함께 저장되거나 함께 버려지므로, 같은 이동으로 두 번 보상받지 않습니다.
- **승인 경계.** 모든 쓰기는 `InteractionGate`가 발급한 세션 토큰을 트랜잭션 안에서 다시 확인합니다. 주행 제한이나 백그라운드 전환 뒤에는 이전 화면에서 시작한 건설이 저장되지 않습니다.
- **차량 GPU 아껴 쓰기.** 마을을 끝까지 지어도 삼각형은 약 9.7만 개이고 텍스처는 쓰지 않습니다(정점 색상). SSAO·bloom·MSAA는 끄고, 장면이 바뀌거나 건설 연출이 움직일 때만 다시 그립니다. 화면이 멈춰 있거나 주행 중·백그라운드일 때는 3D를 그리지 않습니다.

## 제출 APK

- 위치: [`apk/1.60M_ChagokTown_release.apk`](apk/1.60M_ChagokTown_release.apk)
- 차량용 release 빌드(`vehicleRelease`), 버전 0.8.1-balance(versionCode 9), 패키지 `com.chagoktown`
- release 키로 서명(APK Signature Scheme v2), R8 축소 적용. 네이티브 라이브러리는 `arm64-v8a`·`x86_64`
- 차량 전용 APK입니다(`android.hardware.type.automotive` 필수). 휴대폰에서는 아래 [시연 빌드](#소스에서-빌드)를 사용하세요.

## 테스트 환경

개발과 검증에 사용한 Pleos Connect 에뮬레이터입니다.

| 항목 | 값 |
| --- | --- |
| Pleos Connect 에뮬레이터 | **v2.1.0** (빌드 `release_connect_v2.1.0`, Android 14 / API 34 Automotive, x86_64) |
| 화면 규격 | **2560×1440, 160dpi(mdpi)**, 기기 프로필 `Pleos_Connect_v2_0`. 앱 영역 2560×1300 |
| AVD 설정 | RAM 4GB, CPU 4코어, Graphics: Hardware(host GPU), Cold boot |
| Android Emulator | 37.2.13 |
| 차량 신호 | 에뮬레이터 내장 Virtual Console(기어, 누적 주행거리) |

## 실행 방법 (Pleos Connect 에뮬레이터)

1. 에뮬레이터를 켜고 APK를 설치·실행합니다.

   ```bash
   adb install -r apk/1.60M_ChagokTown_release.apk
   adb shell am start -n com.chagoktown/com.chagoktown.ui.MainActivity
   ```

   런처의 앱 목록에서 실행해도 됩니다. 기어가 P일 때 3D 마을이 열립니다.

2. 차량 신호를 넣으려면 Virtual Console을 엽니다. **페이지가 열려 있는 동안만** 신호가 전달됩니다.

   ```bash
   adb forward tcp:8088 tcp:8088
   ```

   브라우저에서 `http://127.0.0.1:8088/` → **Emulation Controls**에서 `Gear Selection`, `Odometer`를 사용합니다.

3. 확인 순서

   | 조작 | 기대 결과 |
   | --- | --- |
   | 기어 P에서 앱 실행 | 마을이 열림. 작은 집 L1, 마을 조각 3개 |
   | 마을 이름 옆 **톱니(설정) → 차량 정보 사용** 켬 | "이동 확인을 시작했어요" (지금 주행거리를 기준으로 저장) |
   | 기어 **D** | 시스템 차단 화면 아래에서 앱도 플레이와 3D를 멈춤 |
   | Odometer를 **1km 이상** 올린 뒤 기어 **P** | "이동이 확인돼 마을 조각 3개를 받았어요" |
   | 목록에서 건물 선택 → **건설하기** | 조각을 써서 건물 L1. 앱을 다시 열어도 유지 |
   | 설정 → **위치 사용** 켬 | 위치 권한 창 → "앱 사용 중에만 허용" |
   | 지은 건물 선택 → **이 건물에 장소 연결하기 → 지금 위치와 연결** | "지금 주차한 곳을 이 건물과 연결했어요" |

필요한 설정:

- 차량 정보·위치 사용은 처음에 **꺼져 있으며** 앱 설정에서 각각 켭니다. 위치 권한은 위치 사용을 켤 때 요청합니다.
- 이동 보상은 하루 한 번입니다. 같은 날 다시 이동하면 "오늘 이동 보상은 이미 받았어요"가 표시됩니다.
- 인터넷 연결이나 계정은 필요 없습니다.

## 소스에서 빌드

필요한 것: JDK 17, Android SDK(API 36, build-tools 36.0.0). `ANDROID_HOME`을 설정하거나 `android/local.properties`에 `sdk.dir`을 적어 주세요.

```bash
cd android
./gradlew :game:test :app:testDemoDebugUnitTest :app:assembleDemoDebug
```

Windows에서는 `.\gradlew.bat`를 사용합니다. 시연 빌드를 설치하고 실행하려면:

```bash
adb install -r app/build/outputs/apk/demo/debug/app-demo-debug.apk
adb shell am start -n com.chagoktown.demo/com.chagoktown.ui.MainActivity
```

시연 빌드 화면 위쪽의 버튼으로 차량 없이 흐름을 확인할 수 있습니다.

- **시연 재료 +60**: 한 번만 받을 수 있는 시연용 조각
- **주행 제한 시험 / 주차 상태로 복귀**: 주행 중 잠금 전환
- **출퇴근 이동 +12km**, **다음 날**: 가상 주행거리와 날짜를 바꾼 뒤 이동 확인

차량용 빌드(`:app:assembleVehicleDebug`, `:app:assembleVehicleRelease`)는 Pleos 공개 Maven 저장소(`nexus-playground.pleos.ai`)에서 SDK를 받습니다. 실행하려면 Android Automotive 기기나 Pleos Connect 에뮬레이터가 필요합니다.

release 서명 정보는 저장소에 포함하지 않습니다. 직접 서명하려면 `android/keystore.properties`를 만들어 주세요. 이 파일이 없으면 서명되지 않은 release APK가 만들어집니다.

```properties
storeFile=../path/to/release.jks
storePassword=...
keyAlias=...
keyPassword=...
```

기기 연결 테스트(`:app:connectedDemoDebugAndroidTest`)는 **시연 앱의 저장 데이터를 지웁니다.** 남길 데이터가 있으면 먼저 백업하세요.

## 검증 현황

| 수준 | 상태 |
| --- | --- |
| JVM 단위 테스트 (game, demo, vehicle) | 통과 |
| 일반 Android 에뮬레이터 (API 36) | 기기 연결 테스트 통과. 기존 저장을 유지한 업데이트 설치 확인 |
| Pleos Connect v2.1.0 에뮬레이터 | 기기 연결 테스트 통과. 주차↔주행 전환, 주행거리 보상, 위치 연결, 차량 서비스 재시작을 Virtual Console 가상 신호로 확인 |
| 제출 APK (vehicle release) | Pleos Connect v2.1.0 에뮬레이터에 설치해 위 확인 순서대로 실행: 주차↔주행 잠금, 주행거리 기준·보상, 건설과 재실행 후 저장 유지, 위치 권한·장소 연결 확인 |
| 실차 | **미검증** |
| 재미·장기 플레이 | **미검증** |

최소 이동 거리 1.0km, 위치 정확도 100m 같은 값은 실차 측정 전의 임시값입니다.

## 남은 일

- 실차 검증: 주행거리 갱신 시점과 반올림, 실제 위치 정확도, 차량 화면 가독성, 3D 프레임 속도·발열·메모리
- Pleos 스토어 심사 대응
- 시즌을 마친 뒤의 콘텐츠
