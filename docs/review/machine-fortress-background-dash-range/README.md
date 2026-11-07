# 기계 요새 배경 채움·화면 높이 비례 돌진 — Issue #34

[Issue #34](https://github.com/26aiera11-cpu/helicopter-game/issues/34) 전체 본문과 [추가 확정 댓글](https://github.com/26aiera11-cpu/helicopter-game/issues/34#issuecomment-6703578301)을 확인했다. **본문의 기존 2배 확대·고정 돌진 시간은 폐기하고, 사용자의 최신 요청 및 댓글의 H×40% / H×70%를 최종 사양으로 적용했다.** 기존 40px 크기/고유 AI 버전 `e6f6f8822a47daf023616681768c3db212d16435`와 이미 생성된 `fix/machine-fortress-background-dash-range`가 기준이다. main 및 기존 기능 브랜치를 변경하거나 병합·Pages 배포하지 않는다.

## 최종 돌진 사양

| 화면 높이 H | 나사봇 거리 | 이동 시간(100px/s) | 톱니벌 거리 | 이동 시간(145px/s) |
| ---: | ---: | ---: | ---: | ---: |
| 320px | 128px | 1.280초 | 224px | 약1.545초 |
| 360px | 144px | 1.440초 | 252px | 약1.738초 |
| 412px | 164.8px | 1.648초 | 288.4px | 약1.989초 |

`config.js`에서 기존 `dashTime`을 제거하고 나사봇 `dashHeight:.40`, 톱니벌 `.70`을 설정한다. `combat.js`는 현재 게임 높이 H를 곱해 목표 거리를 만들고, 실제 안전 경계까지 잘라낸 경로의 길이를 속도로 나누어 돌진 시간을 계산한다. 고정70/188.5px 또는 고정.70/1.30초를 사용하지 않는다.

예고선과 실제 돌진이 같은 시작점·방향·끝점·길이를 공유한다. 나사봇은 예고 시작 때 방향을 고정하고, 톱니벌은 기존처럼 예고 종료 때 방향을 고정한다. 돌진 중에는 플레이어가 반대편으로 움직여도 추적하지 않는다. 경계에 닿으면 예고 경로와 실제 이동을 함께 단축하고, 단축한 길이/속도에 맞춰 종료한다. 벽에 닿은 뒤 원래 목표 시간만큼 추가로 멈춰 있지 않는다.

경고.45/.60초, 쿨다운/휴식2.2/2.6초, HP1/1, 기본 추적46/50, 돌진100/145px/s, 기존 몸체 접촉 피해/무적/r16, 혼합 확률 및 생성 간격/수량은 유지했다. 드론·포탑 및 기가코어는 변경하지 않는다. 이동 시간이 길어져 전체 공격 주기가 늘어나는 것은 확정된 거리 증가의 결과이며 별도 대기 시간을 더하지 않았다. 경계가 없는 경로에서 예고+돌진+회복은 나사봇 약3.93~4.298초, 톱니벌 약4.745~5.189초다.

기존1/300초 적분을 유지해 상태 전환 시점은 최대 약3.33ms 단위로 표시되지만 도착 위치는 정확한 경로 끝점에 고정한다. 화면 크기가 바뀌면 기존 안전 취소/1.2초 휴식을 사용하고 다음 예고에서 새 H를 적용한다. 세로 방향으로 화면 중앙에서 출발하는 톱니벌은 .70H보다 먼저 경계에 닿으므로 해당 방향은 단축되는 것이 정상이다. 가로 방향의 중앙 출발에서는 세 테스트 화면 모두 전체 목표 거리를 충족했다.

## 배경 좌우/상하 채움

승인된 `machine_fortress_background_approved.png`의1672×941 원본 바이트·매니페스트를 유지한다. 중앙은 기존 `min(w/imageWidth,h/imageHeight)` contain 좌표 그대로 전체 원본을 선명하게 그린다. 중심 피벗/비율/중요 문양을 잘라내거나 원본을 cover로 바꾸지 않았다.

남는 영역에는 같은 원본으로 만든 보조 cover 레이어를 먼저 그린다. 보조 레이어만10px 상당으로 부드럽게 흐리고12% 어둡게 처리해 원본 디자인과 연결한다. 가장자리40px 상당을 여유 있게 그려 블러의 투명 테두리를 막는다. DPR에 맞는 오프스크린 Canvas에 캐시해 크기/DPR가 같으면 매 프레임 새 블러/Canvas를 생성하지 않는다. 원본 비율과 정확히 같으면 보조 레이어를 생략한다.

Canvas `filter`를 지원하지 않으면 같은 이미지를 작은 Canvas로 부드럽게 축소·확대해 보조 채움에만 사용한다. 어느 방식도 가운데 원본을 흐리거나 어둡게 하지 않는다. 배경 레이어는 Canvas 내부에만 있고 HUD·조작 버튼의 입력 영역을 바꾸지 않는다. 이미지가 아직 로드되지 않은 순간에만 기존 기본색 fallback을 사용한다.

## 보호한 파일과 기능

실제 게임 코드 변경은 다음3파일의 허용 차분뿐이다.

- `assets/machine_fortress/config.js`: 두 종의 고정 시간→화면 높이 비율.
- `assets/machine_fortress/combat.js`: H비례 경로/시간 산출 및 검사 가능한 snapshot 수치.
- `assets/machine_fortress/machine_fortress.js`: 캐시된 보조 배경, 기존 중앙 contain 표시 유지.

**index.html은 기준과 바이트가 같다.** [보존 검사](preservation.json)는 기존128자산 중125개가 원본 바이트를 유지하고 위3파일도 정확한 허용 차분만 제거하면 기준과 일치함을 확인한다. PNG11개/원본 manifest/음원/다른 지역 전투·배경/플레이어/조작/아이템/점수 파일은 변경하지 않았다. 기존 원본 해시는 덮어쓰지 않고 새 차분 역변환을 기존 보존 검사 앞에 연결했다.

일반40px/기가코어132px, 실제 일반 충돌r16(지름32px)과 외형의 차이, 기존 x17/y18 경계에서 외형 일부가 잘릴 수 있는 한계도 그대로다. 기가코어 HP20/기본 단발/2000점/보상/소멸, 기존 월드1 20단계·확장40단계·개발자 바로 시작, 선택화면·음악·점수/기록·아이템 유지·자이로·조이스틱·전체화면·종료 확인창을 보호했다.

## 검증

**등록72모음 중 관련16개를 실행해15통과/1기존 미해결 실패·완료255그룹**이다. 신규 집중 검사12/11그룹, 기존 기계 요새 전투22/22그룹, 그래픽/보스13/13그룹은 모두 통과했다. 최종 모음별 수치는 [test-summary.json](test-summary.json), 원문·최초 실패는 `tests/` 아래에 기록한다. 실패 이전 부분그룹 및 중복 실행은 완료 합계에 넣지 않았고 전체72모음 재실행은 아니다.

- 신규 집중 검사: 일반 브라우저12그룹/독립 HTML11그룹. 세 높이×두 종×8방향=48경로에서 목표 거리·실제 속도·동적 시간·방향 고정·예고선 끝점·기존 회복 시간을 확인했다. 경계2px 경로는 실제2px만 이동하고 시간도2/100·2/145초로 줄어든다.
- 배경:915×412/800×360/568×320/1672×941/412×915와DPR1/2의10조건. 모든 픽셀 알파255·다양한 이미지 가장자리·기본색이 아닌 네 모서리를 확인하고, 중앙 원본 내부 픽셀은 별도 contain 참조 이미지와 차이0이었다. 원본 전체를 쓰는 실제 drawImage 좌표도 비교했다.
- 원본 비율에 아주 가까운398×224/597×336/645×363/812×457의 추가DPR2 검사에서도 모든 픽셀 알파255를 확인했다. [추가 수치](near-aspect-extra.json).
- Canvas filter 미지원 모의 조건/DPR2, 캐시 재사용, 실제DPR2 1136×640 Canvas, 돌진 중 리사이즈와 세로→가로 복귀를 검사했다. 기준3모듈을 Git에서 그대로 제공하는 별도 URL과 현재 URL의 실제 게임 화면을 비교했다.
- 기존 기계 요새 전투 일반/오프라인, 그래픽/보스 일반/오프라인, 월드 진행·개발자 시작·기존 지역·음악·모바일 조작·독립 HTML을 회귀 검사한다. 새 높이 비례 사양으로 옛35/94.25px 기대값만 갱신했으며 기존 보호 검사를 제거하지 않았다.

초기 경계 fixture는 나사봇의 근접 감지110px 밖인120px에 플레이어를 두고 돌진을 기다려 실패했다. 플레이어를80px로 옮겨 요청한 경계 돌진 상황을 만들었으며 **게임의 감지 거리나 전투 수치는 바꾸지 않았다.** 실패 이전6부분그룹·원문·결과를 `tests/initial-native/`에 보존하고 최종 통과 합계에는 넣지 않는다.

기존 **Issue #30 설원 긴3점 멀티터치 이후 나가기 click 누락**이 이번 worlds에서도16부분그룹 뒤 다시 재현됐다. [현재 이벤트 추적](tests/worlds/exit-touch-failure.json)·[실패 화면](tests/worlds/exit-touch-failure.png)·[실패 원문](tests/worlds/run.log)을 보존하며 낮은 우선순위 별도 미해결로 유지한다. 조작 코드는 수정하지 않았고 이16부분그룹을 완료 합계에 넣지 않았다. 정상20/40단계·세 캐릭터 진행/점수/아이템은 해당 모음의 실패 이전 부분에서 통과했지만 전체 모음은 실패로 처리했다. [과거 실패](../machine-fortress-normal-combat/tests/worlds/exit-touch-failure.json)도 보존한다.

이 검사는 실제 Chromium에 제어 입력/시간을 넣은 결과다. 실물 Galaxy Samsung Internet/Chrome의 센서/멀티터치·장시간 FPS·최종 회피 난이도·로컬 파일 연결은 미검증이다. 서버 CPU 수치나 Canvas 모의DPR를 실물 승인으로 표현하지 않는다.

## 전후 화면·공격 자료

| 화면 | 수정 전 | 수정 후 |
| --- | --- | --- |
| 915×412 | [단색 좌우 여백](tests/machine_background_dash-native/before-background-915x412.png) | [이미지 확장 채움](tests/machine_background_dash-native/after-background-915x412.png) |
| 568×320 | [기존 표시](tests/machine_background_dash-native/before-background-568x320.png) | [확장 표시](tests/machine_background_dash-native/after-background-568x320.png) |

[나사봇 예고](tests/machine_background_dash-native/screw-warning.png) · [나사봇 돌진](tests/machine_background_dash-native/screw-dash.png) · [톱니벌 예고](tests/machine_background_dash-native/wasp-warning.png) · [톱니벌 돌진](tests/machine_background_dash-native/wasp-dash.png) · [실제DPR2](tests/machine_background_dash-native/after-dpr2-568x320.png).

화면은 실제 게임 Canvas 캡처이며 원본 PNG를 가공해 만든 합성 화면이 아니다. 보조 레이어는 원본 전체를 보존하기 위한 주변 채움으로, 가운데의 승인된 선명한 프레임과 구분된다.

## 갤럭시 테스트 파일

[단일 HTML](../../../dist/heli_trio_galaxy_test.html)은 **76,797,394바이트**, SHA256 `7f98c3acda119817c013446562164cc7bd017a2c475fcd5d10159940a2ae887f`다. ZIP은 **56,141,901바이트(약53.54MiB)**, SHA256 `e1d8460a2b8a181c637b27e276c4531289be577be4090810c95aa19ab6d6ee75`다. 기존 빌드/패키지 스크립트로 현재 소스를 재생성했고 스크립트 자체는 변경하지 않았다.

- [갤럭시 ZIP 다운로드](https://raw.githubusercontent.com/26aiera11-cpu/helicopter-game/refs/heads/fix/machine-fortress-background-dash-range/dist/heli_trio_galaxy_test.zip)
- [빌드](build.json) · [ZIP CRC/크기](package.json) · [별도 압축해제/내장 바이트 검사](embedded-verification.json)

ZIP에는 최신 HTML 한 개만 있다. 별도 디렉터리 압축해제 후 전체 HTML 바이트 일치·CRC,26스크립트와 현재 기계 요새4모듈, 승인 PNG11개와 기존 외부음원5파일의 원본 내장, 원본 manifest와 복구 Storm 배경을 확인했다. 기계 요새 설정의 고정 `dashTime` 부재와 `.40/.70` 비율도 확인했다. 네트워크를 끈 동일 HTML 실행에서 외부 요청0을 검사했다. 관리 환경 file:// 제한을 우회하지 않고 빈 origin에 실제 HTML을 주입한 오프라인 검사이며 실물 파일 열기는 별도 확인 대상이다.

보고서 JSON의 큰 data URI가 있으면 공개 사본에서 MIME/길이/SHA256으로 치환하며 수치/상태/실패는 보존한다. 원본·공개 사본 해시는 `artifact-manifest.json`에 기록한다. 실제 게임 자산과 배포용 파일은 이 과정에서 변형하지 않는다.

기가코어 특수 공격·폭주 강화·전용 음악은 이번 범위에 포함하지 않는다. 지정 브랜치에만 커밋·푸시하고 원격 ZIP을 직접 다운로드해 확인하며, main 병합과 GitHub Pages 배포는 하지 않는다.
