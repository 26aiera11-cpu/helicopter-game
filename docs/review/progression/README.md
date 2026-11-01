# 게임 오버·보스 체력·아이템 보존 검증

기준 `9c3c5a8aab571a15abd417c44f7894dd334dca20`, 작업 브랜치 `feature/selection-screen-integration`.

- `50a070a`: 사망 즉시 진행/음악 정지 → 마지막 화면에 GAME OVER·별 3초 → 원래 선택화면 복귀. 중복 타이머/입력을 차단하고 selectionResult는 최종 클리어만 복사한다.
- `80800c3`: 등장 시 기본 보스 HP × 강화별 **1.0/1.1/1.4/1.6/1.9/2.2**. 전투 중 강화 변화로 HP를 다시 올리지 않는다.
- `646f9ba`: nextPhase의 아이템 초기화만 제거한다. 종류/좌표/남은 수명·접촉 획득/만료를 유지하고 새 게임에서는 초기화한다.
- 점수 개선은 DEVELOPMENT_LOG.md 예정 목록에만 기록했다. 별 점수, 캐릭터/적/보스/배경/탄환 이미지와 음원, 이동·공격·강화 효과·보스 패턴·보상·전체화면·나가기 확인창은 보존했다.

## 실제 실행 결과

| 검사 | 통과 그룹 |
| --- | ---: |
| [game_over](game-over/test-results.json) | 7 |
| [boss_balance](boss-balance/test-results.json) | 4 |
| [items](items/test-results.json) | 7 |
| [selection](regression/selection.json) | 15 |
| [game_audit](regression/game-audit.json) | 11 |
| [trio](regression/trio.json) | 9 |
| [tanko](regression/tanko.json) | 8 |
| [bgm](bgm/test-results.json) | 9 |
| [boss_reward](boss-reward/test-results.json) | 8 |
| [exit_dialog](exit-dialog/test-results.json) | 10 |
| [fullscreen](fullscreen/test-results.json) | 7 |
| [standalone](../galaxy-test/test-results.json) | 19 |

**총 114개 그룹 통과.** 실제 Chromium/Playwright 및 Node 문법 검사. [요약 JSON](test-summary.json).

게임 오버 복귀는 3001.2ms였다. 2.7초까지 표시·동결되고 3초 후 원래 제목/선택 UI가 복원된다. 마지막 캔버스/상태 정지, 동시에 닿는 회복 아이템으로 부활하지 않음, 중복 사망/이전 타이머 취소, 반복 시작/종료, 실제 네이티브 전체화면·게임 내부 종료 모달을 확인했다. BGM은 사망 직후 8개 트랙 모두 paused, 재생 시계 정지, 재시작 1개 트랙, 음악 OFF 유지·4지역/보스 전환·12회 추가 반복 최대 동시 1개를 검사했다. 이는 스피커 청취 검사가 아니다.

보스는 288회 비교와 72개 등장 HP 고정 검사를 통과했다. [모든 캐릭터·4지역·강화0/1/3/5 변경 전/제안식/최종 처치 시간](boss-balance/boss-ttk-comparison.md). 120Hz·60Hz에서 0강은 기존과 같고, 모든 표본 강화 캐릭터가 해당 무강화보다 빨랐다. 기존 적 체력/탄환·보스 1/3/3/5발 패턴·보상 50:50/한 번 지급·보상→지역 +2HP 순서·체력바를 유지했다.

아이템은 20개 직접 전환과 실제 일반 적/보스 처치 전환을 검사했다. 객체/수명/좌표가 전환 자체로 바뀌지 않고 정상 시간만 차감된다. 만료/접촉 +2HP·+1강화/최대치/한 번 제거·새 게임 초기화가 정상이다. 전체 20개 웨이브·4보스 진행에서 기존 별 160을 확인했다.

## 갤럭시 결과물

[ZIP 다운로드](https://github.com/26aiera11-cpu/helicopter-game/raw/refs/heads/feature/selection-screen-integration/dist/heli_trio_galaxy_test.zip?download=1) · [실행 안내](../galaxy-test/README.md) · [압축/최신 기능 무결성 증명](package-verification.json).

HTML/ZIP을 최신 소스로 다시 만들었다. ZIP에는 HTML 1개만 있으며 CRC·unzip -t·실제 추출 후 바이트 일치·3초 연출/최종 보스 배율/아이템 보존/새 게임 초기화를 확인했다. 원본 인라인 JS 3개와 선택 JS를 그대로 내장했고 외부 의존성/오프라인 요청/실패 자산/잡히지 않은 JS 오류/기본 대화상자는 0건이다.

## 한계·남은 사항

- 실제 갤럭시 삼성 인터넷/Chrome, file:// 파일 연결, Android 주소창/가로잠금/센서·성능·스피커 청취는 미검증이다. 관리형 Chromium 정책이 file://를 막아 같은 HTML을 새 페이지에 주입하고 네트워크를 끈 상태로 검사했다. 정책을 우회하지 않았다.
- 처치 시간은 같은 거리에서 매 틱 보스 중심을 조준한 제어 비교다. 사람의 전투 난이도/수동 연속 완주가 아니다.
- 숲 5강 트리오는 최종 1.142초로 여전히 빠르다. 공통 체력을 더 올리면 탱코 5강이 무강화보다 느려질 수 있어 2.2배로 제한했다. 공격 효과 보호 조건 안에서의 조정이다. 3강보다 5강이 반드시 빠르다는 조건은 보장하지 않는다.
- 백그라운드 앱 전환 중 3초 타이머는 브라우저 정책에 따라 늦게 실행될 수 있다.
- main 병합·GitHub Pages 배포는 수행하지 않는다.

## 화면

![915×412 마지막 화면 위 게임 오버](game-over/game-over-915x412.png)

![결과가 남지 않은 선택화면](game-over/clean-selection-after-game-over.png)

![568×320 게임 오버 패널](game-over/game-over-568x320.png)
