# Windows에서 APK/AAB 빌드

앱 이름은 **헬리 트리오**, 임시 테스트 ID는 `com.helitrio.offlinetest`다. 정식 스토어 등록 전에 앱 ID를 사용자와 확정한다. 이 작업은 스토어 업로드를 포함하지 않는다.

## 준비

- Node.js 22 이상(현재 검증 환경 24), JDK **21 전체 개발 도구**. `java -version`과 `javac -version`이 모두 21이어야 한다. Java 실행 환경만 설치하면 컴파일할 수 없다.
- Python 3.10 이상. 웹 자산 생성 스크립트에 사용하므로 `python --version`도 확인한다.
- Android Studio의 SDK Manager에서 Android 16 / API **36**, Build-Tools **36.0.0**, Platform-Tools를 설치하고 SDK 라이선스에 동의한다.
- 저장소를 `feature/android-capacitor-first-build` 브랜치로 받는다. 기존 Android 프로젝트를 다시 생성하지 않는다.
- `JAVA_HOME`은 JDK21 폴더, `ANDROID_HOME`은 SDK 폴더를 가리키게 한다. Android Studio가 만든 `android/local.properties`도 사용할 수 있다. 이 파일과 개인 경로는 Git에 올리지 않는다.

PowerShell 예시(설치 경로는 PC에 맞춘다):

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
& "$env:JAVA_HOME\bin\javac.exe" -version
npm ci
npm run android:sync
cd android
.\gradlew.bat :app:assembleDebug
```

첫 빌드는 npm/Maven/Gradle 의존성을 인터넷으로 내려받는다. 완성된 앱의 게임 실행에는 인터넷이 필요하지 않다. 의존성 캐시가 준비된 이후에는 `--offline`으로 빌드할 수 있다.

출력: `android/app/build/outputs/apk/debug/app-debug.apk`. 공유용 산출물은 저장소의 `dist/android/heli_trio_debug.apk`에 둔다. **Debug APK는 테스트용 키로 서명된 설치 파일**이며 출시용 서명 결과가 아니다.

## 갤럭시 설치

1. APK를 휴대폰으로 다운로드해 파일 앱에서 연다. 필요한 경우 해당 파일 앱의 ‘알 수 없는 앱 설치’ 허용을 확인한다.
2. 실행 후 가로 화면·선택화면·첫 터치 음악을 확인하고 게임을 시작한다.
3. 개발 테스트의 지역 바로 시작을 사용하면 장시간 진행 없이 각 지역·보스를 확인할 수 있다. 개발 테스트 결과는 원래처럼 순위표에 저장하지 않는다.
4. USB 디버깅을 사용한다면 `adb install -r app-debug.apk`로 같은 서명의 APK를 덮어쓸 수 있다.

다른 PC에서 생성한 debug 키는 서명이 다를 수 있어 기존 APK를 업데이트하지 못한다. 설치된 앱을 삭제하거나 앱 데이터를 지우면 앱 내 순위표도 사라진다. 업데이트에는 같은 서명키와 앱 ID를 사용한다. 개인 키는 저장소 밖에서 보관하며 GitHub나 채팅에 올리지 않는다.

앱의 점수는 WebView의 로컬 저장소에 남는다. 기존 브라우저/GitHub Pages 기록은 별도 저장소이며, 앱 설치가 그 기록을 가져오거나 삭제하지 않는다.

## AAB: 서명 전과 서명 후

```powershell
# 먼저 저장소 루트에서 npm run android:sync 실행
cd android
.\gradlew.bat :app:bundleRelease
```

현재 release 서명 설정이 없으므로 `android/app/build/outputs/bundle/release/app-release.aab`는 **서명 전 빌드 결과**다. AAB는 APK처럼 휴대폰에서 직접 설치하는 파일이 아니다.

출시 후보를 만들 때는 Android Studio의 **Build → Generate Signed App Bundle / APK → Android App Bundle**을 사용한다. 사용자 소유의 키와 비밀번호를 로컬에서 입력하고, 서명된 출력 경로를 확인한다. 키·비밀번호·keystore/signing 설정은 Git에 커밋하지 않는다. Google Play 계정·Play App Signing·스토어 업로드는 별도 승인 후 진행한다.

## 실기기 확인 항목

- 비행기 모드에서 첫 실행과 재실행, 모든 지역 이미지·음원 누락 여부.
- 가로 고정, 노치 양옆 여백, 시스템바 잠시 표시 후 복원, 나가기·선택화면 복귀.
- 센서 켜기/중앙 보정 후 상하좌우 방향·감도. 웹 센서가 없으면 중력 센서 브리지가 기존 계산을 사용한다. 자동 검사만으로 실제 센서 작동을 보증하지 않는다.
- 센서 이동 + 회전 조이스틱 + 발사 동시 입력, 드래그 + 회전 + 발사, 손가락 해제 후 입력 잔존 여부.
- 홈/화면 잠금 후 음악 정지, 복귀 확인 후 계속 플레이, 음악 OFF·효과음 설정 유지.
- Android 뒤로 가기: 플레이 중 기존 확인창, 취소/선택화면, 선택화면의 앱 종료 확인, 중복 종료 방지.
- 게임 오버 3초·재시작·최종 결과 및 앱 재실행 후 점수 보존.
- 기가코어 장벽·마그마 드래곤 브레스 등 긴 전투의 성능과 탱코 회피. 이번 작업은 밸런스를 변경하지 않았다.

compile/target SDK36, min SDK24다. APK의 JNI `.so` 포함 여부와 ZIP 정렬을 검사하며, 네이티브 라이브러리가 없으면 해당 ELF 16KB 페이지 검사는 적용 대상이 없다. 실제 16KB 기기 실행과 스토어 심사는 별도 확인이다.
