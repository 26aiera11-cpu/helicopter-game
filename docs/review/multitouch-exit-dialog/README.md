# Issue #30: 멀티터치 후 나가기 확인창

작업 브랜치: `fix/multitouch-exit-dialog` · 기준: `3c085442bba6490bfa41cae64ac4007af570ba2e` · 2026-11-07 KST.

[Issue #30 최신 확정 댓글](https://github.com/26aiera11-cpu/helicopter-game/issues/30#issuecomment-6707611342)을 적용했다. 현재 브랜치와 원격이 모두 승인된 기본40단계 커밋에서 출발하는지 확인했다. main 병합/Pages 배포/강제 푸시는 하지 않는다.

## 재현과 원인 범위

수정 전 실제 기존 `worlds` 검사를 다시 실행해 **16부분 그룹 후 설원 멀티터치→나가기 실패**를 재현했다. [원본 상태와 이벤트](tests/baseline-worlds/worlds/exit-touch-failure.json), [실패 로그](tests/baseline-worlds/worlds/run.log), [실패 화면](tests/baseline-worlds/worlds/exit-touch-failure.png)을 보존했다. 기존 개발 기록의 실패 자료도 수정하지 않았다.

나가기 버튼의 pointerdown/up은 있었지만 **가장 이른 window capture에서도 click이 관측되지 않았다**. 버튼은 hit test 대상이고 disabled/inert가 아니었으며, 입력 소유자도 해제된 상태였다. 따라서 확인창의 click 콜백이나 document 단계의 전역 게임 클릭 차단이 이 관측된 click을 직접 삼켰다고 단정할 수 없다. 브라우저의 호환 click 생성 여부와 긴 테스트 시퀀스/입력 주입의 영향은 남아 있다.

별도 72조건씩 두 차례 비교에서는 모두 click이 생성됐다. 각 비교는 게임 나가기/게임 안의 단순 기본 button 48조건과 분리된 기본 HTML button 24조건이다. 2·3·4점 터치, 마지막 touchEnd의 빈 배열/해제 점 배열, ID 재사용/신규, CDP/Playwright tap을 비교했다. 한 번은 window의 Pointer/Click 최소 계측, 다른 한 번은 window/document/target의 Touch/Pointer/Mouse 캡처·버블 계측이다. [최소 계측](diagnosis/minimal-listener-matrix.json), [전체 계측](diagnosis/full-listener-matrix.json)에 결과를 기록했다. 재현 스크립트는 해당 폴더에 있으며 index는 기준 커밋에서 제공한다.

초기 탐색의 [비분리 프로브](diagnosis/initial-non-isolated-probe.json)는 게임 문서에 set_content를 사용해 전역/리스너가 완전히 분리되지 않았다. 그 24개 기본-button 사례를 독립 HTML 검증으로 계산하지 않았다. 이후 새 about:blank 문서에 계측을 다시 설치해 분리했다. 첫 탐색의 게임 update 정지 조건도 정상 실시간 게임 재현과 구분한다.

**CDP touchEnd 배열 형식 하나만이 원인이라는 결론이나 삼성 인터넷 실기기 해결 보장은 하지 않는다.** 설치된 CDP 문서는 touchEnd/Cancel에 빈 배열을 명시하지만, Chromium은 해제 점 배열도 수용했다. 기존 실패 테스트의 입력 방식과 단언을 삭제/완화하지 않고 제품 코드의 유효한 버튼 터치만 보완했다.

## 최소 수정

실행 코드 변경은 `index.html`의 기존 나가기 click 등록 부분뿐이다.

- 기존 종료 콜백을 그대로 공유한다. 정상 click은 즉시 처리한다.
- 나가기 버튼에서 시작·종료한 단일 primary touch, 동일 pointerId, 12 CSS px 이내 이동, 750ms 이내 해제만 인정한다.
- 정상 click에 100ms 우선권을 주고, click이 없을 때만 확인창을 연다. 전역 synthetic click이나 preventDefault를 추가하지 않았다.
- 다중 접촉, 드래그, 길게 누름, pointercancel, 해제 전 capture 유실은 제외한다. 취소/메뉴/게임오버/blur/resize/전체화면 전환 등에 대기 처리를 취소한다.
- 이미 사용한 터치의 늦은 click은 재처리하지 않는다. Cancel 후 새 터치는 즉시 다시 사용할 수 있다.
- 마우스·Enter·Space·보조기술의 기존 click 경로와 기존 모달의 포커스 처리를 유지한다.

`assets/controls/controls.js`의 500ms 게임 클릭 방어, 조이스틱 크기/위치/8% 데드존/감도/최대 회전속도, 자이로·발사·드래그·멀티터치는 **바이트 단위로 그대로**다. 기존131자산 전체와 나가기 콜백, 그 외 index 전체를 기준과 비교한다. 월드1→월드2 기본40/명시20, BGM/PNG, 전투·보상·아이템·점수/저장/전체화면도 변경하지 않았다.

[보존 검사](../../../tests/exit_tap_preservation.py)는 허용한 한 덩어리만 정확히 되돌려 index 전체를 비교한다. 기존 역사별 보존 검사는 이 델타를 먼저 되돌리도록 연결했으며 보호 단언을 제거하지 않았다.

## 테스트와 실패 공개

최종 관련 **24모음 전부 통과·367완료 그룹**이다(등록82모음 전체 실행은 아님). 일반/오프라인 새 검사 각13그룹과 총300회 멀티터치 후 나가기+300회 Cancel 직후 재열기, 의도적 click 유실60회를 통과했다. 보완 지연은100.1~105.8ms였다. 원래 worlds 입력/단언을 바꾸지 않고 수정 후 일반3회 연속 전체20그룹씩, 오프라인1회19그룹을 통과했다. 추가 일반2회의40그룹은 위 최종367그룹에 중복 합산하지 않았다. 모바일/자이로,선택화면/게임오버,내부나가기/전체화면,점수/순위/저장,개발자시작,기본40/명시20,기가코어/음악,아이템/보상/생성,선택화면음악,화산보스와 독립HTML 검사를 실행했다.

최종 실행 집계는 [test-summary.json](test-summary.json), 개별 결과·원본 로그·스크린샷은 tests 아래에 보존한다. 통과하지 않은 시도를 최종 완료 그룹에 합산하지 않는다.

새 검사는 일반 제공 페이지와 네트워크 차단 단일HTML 각각에서 915×412, 800×360, 568×320, DPR1/2를 사용한다. 각 화면에 총50회씩 멀티터치 후 나가기와 Cancel 직후 재열기를 검사한다. 뾰코/빙글/탱코의 실제 player.type을 확인하고 숲/설원/기계요새 보스전에서 2/3/4점 입력, 두 해제 방식, 재사용/새 ID, CDP/Playwright, 해제 후0/100/300/550ms와650ms 길이의 동시 조작을 검사한다.

click 유실/늦은 click은 별도의 **의도적 장애 주입** 검사다. 실제 trusted pointer 입력 후 window capture에서 다음 click만 차단하고 100ms 보완 동작을 측정한다. 이는 해당 브라우저가 항상 click을 누락시킨다는 증거로 사용하지 않는다. down-only/cancel/810ms long press/밖으로 드래그 후 복귀/다중 접촉/blur/resize/메뉴 전환/실제 체력0 게임오버 중에는 열리지 않는지 확인한다. 마우스·Enter·Space·Tab/Shift+Tab, Cancel 포커스 복귀, 확인·전체화면 유지도 검사한다.

초기 검사 자체의 오류도 보존했다. attempt-1은 개발자 모드에서 시험 모드가 강제 해제되는 기존 동작을 잘못 기대했다. attempt-2는 사용하지 않는 캐릭터 변수와 detail 없는 가짜 gameover 이벤트를 사용해 150사례가 실제로는 뾰코만 검사되고 UI 이벤트 오류6회가 발생했다. 이를 세 캐릭터 통과로 집계하지 않았다. 진행 중이던 오프라인 시도는 중단 기록으로 남긴다. attempt-3은 Playwright의 arg 키워드를 빠뜨린 검사 호출 오류다. 최종 검사는 실제 selectedHeli/player.type, 정식 hp=0→update→3초 복귀 경로를 사용한다. attempt-4-offline은 set_content/document.open 후 window 계측이 제거되어 pointerup 기록을 찾지 못한 검사 오류다. 오프라인 HTML 주입 뒤 계측을 다시 설치했다. 제품 코드를 이 검사 오류에 맞춰 변경하지 않았다.

기존 scoring-offline은14부분 그룹 후 반복 HTML 주입 중8GiB 환경의 OOM으로 renderer가 종료됐다(oom_kill2→3). [실패와 당시 소스](tests/attempt-5-scoring-memory/)를 보존했다. 같은 BrowserContext의 실제 localStorage를 유지하면서 이전 Page를 닫아 한 번에 하나의80MB 문서만 검사하도록 검사 도구의 자원 수명만 분리했다. 점수/저장/손상/권한/용량 예외 단언은 유지하며 게임·자산은 바꾸지 않았다.

default_world_route-offline도6부분 그룹(세 캐릭터40단계와 경계/기록 보존) 후 URL별 반복 주입 중 같은 메모리 한도로 종료됐다(oom_kill3→4). [당시 소스/로그](tests/attempt-6-route-memory/)를 보존하고 같은 Page 분리 원칙을 적용했다. 실제 BrowserContext/localStorage와 URL·진행·음악·기록 단언은 그대로 유지했다.

item_spawn_rules의 최초15부분 그룹 후 실패는 옛 기본20단계/30,400점 종료 기대와 현재 기본40의 충돌이었다. [당시 검사/로그](tests/attempt-7-item-legacy20/)를 남기고 해당 기존20단계 시나리오에서 World1-only 옵션을 명시했다. 게임 경로와 모든 생성·보상·점수 단언을 유지했다. 기본40은 별도로 세 캐릭터와 아이템 포함 worlds에서 확인한다.

## 화면 자료

- 수정 전: [설원 나가기 무반응](tests/baseline-worlds/worlds/exit-touch-failure.png)
- 수정 후: [915×412](tests/final-all/multitouch_exit-native/exit-dialog-915x412-dpr1.png) · [800×360](tests/final-all/multitouch_exit-native/exit-dialog-800x360-dpr1.png) · [568×320](tests/final-all/multitouch_exit-native/exit-dialog-568x320-dpr1.png)
- 독립HTML: [568×320 DPR2](tests/retry-final/multitouch_exit-offline/exit-dialog-568x320-dpr2.png)

수정 전 자료는 실패한 설원 화면, 수정 후 자료는 각 검사에서 직접 시작한 숲 보스 위 확인창이다. 기존 화면·이미지·패널 디자인은 유지된다.

## 갤럭시 파일

[build.json](build.json), [package.json](package.json), [압축·내장 무결성](standalone-integrity.json)에 크기와 SHA256을 기록했다. ZIP은 단일 HTML만 포함하며 CRC·실제 폴더 압축해제·HTML 전체 바이트 일치를 확인했다. 원본 PNG11개/음원7개, 현행27스크립트와 새 나가기 처리, 기본40 월드 코드가 그대로 포함된다.

오프라인 검사는 실제 단일HTML을 로컬 origin에 넣은 후 네트워크를 차단한다. 관리 환경의 file:// 접근 제한은 우회하지 않았다. **실제 Galaxy 삼성 인터넷/Chrome의 OS 터치·주소창/전체화면·센서·스피커·다운로드 파일 직접 열기는 별도 실기기 승인 대상**이다. Chromium에서 정확한 실패 재현과 해결 후 반복 통과는 확인하되, 실기기와 CDP의 click 유실 원인이 같다고 주장하지 않는다.

```bash
PYTHONDONTWRITEBYTECODE=1 python tests/exit_tap_preservation.py
PYTHONDONTWRITEBYTECODE=1 python scripts/build_galaxy_test.py
PYTHONDONTWRITEBYTECODE=1 python scripts/package_galaxy_test.py
PYTHONDONTWRITEBYTECODE=1 python tests/run_volcano_checks.py --workers 1 --artifacts /tmp/exit-review --only multitouch_exit-native multitouch_exit-offline worlds worlds-offline mobile_controls mobile_controls-offline exit_dialog fullscreen_smoke selection_smoke game_over scoring scoring-offline developer_start-native default_world_route-native default_world_route-offline machine_boss-native machine_fortress_bgm-native galaxy_standalone item_persistence item_spawn_rules boss_reward selection_bgm selection_bgm-offline volcano_boss-native
```
