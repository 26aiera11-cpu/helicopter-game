# 게임 오버 BGM 정지 오류 N1 수정

2026-11-01(KST) · `feature/selection-screen-integration` · 시작 HEAD `7e5faf5cee3e38e17301fd8746f693b7010934cf`

## 작업 전 확인과 이미지 구분

작업 시작 시 로컬·원격 작업 브랜치는 `7e5faf5`였고 작업 트리는 깨끗했다. 개발 기록의 기존 N1은 ‘게임 오버 경로에서 음악을 정지하지 않음’이었다.

최근 별도로 제작한 **얼굴을 바르게 돌리고 가로 폭을 좁힌 트리오 시안은 아직 게임에 적용되지 않았다.** 현재 게임은 `7e5faf5`의 기존 앞끝 수정 PNG(`assets/gameplay/trio-body-pointed.png`)를 사용한다. 이번 작업은 이미지 적용을 포함하지 않는다. [이미지 상태 확인 JSON](image-status.json).

## 원인과 최소 수정

기존 게임 오버는 `started=false`와 선택화면 표시만 처리했다. 루프에서 음악 tick 호출이 멈춰도 이미 재생 중인 WAV는 계속 재생된다. `gameAudioStarted`도 true로 남았다.

실제 수정 전 브라우저에서 게임 오버 후 선택화면이 보이면서도 BGM 1개가 계속 재생되고, 숲 음악의 `currentTime`이 약 0.131초에서 0.493초로 증가하는 현상을 확인했다. [수정 전 재현 결과](before-fix-reproduction.json).

게임 오버 분기에 다음 **두 문장만** 추가했다.

```js
window.gameAudioStarted = false;
gameAudio.pause();
```

기존 나가기·최종 클리어와 동일한 정지 함수를 재사용한다. 이 함수는 지역·보스 BGM을 멈추고 현재 트랙·지역·보스 상태를 초기화하며 기존 Web Audio 정지도 수행한다. 음악 ON/OFF 설정은 바꾸지 않는다. 새 게임은 기존 시작 함수와 음악 제어기를 그대로 통해 재생한다.

시작 커밋의 `index.html`에 이 두 문장을 삽입한 전체 파일과 현재 파일이 일치하는지 확인했다. 이미지·공격·이동·단계·보스·아이템·강화·전체화면·종료 모달·음악 전환 제어기는 변경하지 않았다. WAV 12개와 모든 자산의 바이트/SHA-256을 보존했다.

## 실제 브라우저 테스트

Chromium/Playwright에서 실제 터치 사용자 동작과 네이티브 `HTMLAudioElement`를 사용했다. 재생·정지 메서드나 자동 재생 정책을 가짜 구현으로 바꾸지 않았다. 관찰용 래퍼만 설치해 미디어 상태·이벤트·시간을 확인했다.

| 요청 상황 | 확인 결과 |
| --- | --- |
| 게임 시작 | 숲 BGM 1개, 볼륨 0.42, 실제 재생 시간 증가 |
| 체력 0 | BGM 모두 paused, 시작 플래그 false, 재생 시간 정지 |
| 선택화면 복귀 | 무음 상태 유지, 음악 ON 설정 유지, 화면 복귀 알림에도 재생 안 됨 |
| 다른 캐릭터 재시작 | 빙글로 숲 BGM 1개 정상 재생, 기존 체력 유지 |
| 음악 OFF | 탱코·트리오로 재시작해도 BGM 0개, 게임 오버 뒤에도 OFF 유지 |
| 보스·단계 전환 | 네 지역 BGM↔보스 BGM 전환, 기존 등장 효과·다음 지역 이동 유지, 최종 클리어 정지 |
| 반복 게임 오버·재시작 | 추가 12회, 세 캐릭터 순환, 동시 BGM 최대 1개·중복 관찰 0건 |

음악을 선택화면에서 다시 ON으로 바꿔도 종료된 게임의 음악은 바로 재생되지 않고, 다음 시작에서 정상 재생됐다. 기본 WAV 요소 12개를 재사용했으며 BGM은 그중 반복 트랙 8개를 관찰했다. 비반복 효과음의 의도된 겹침은 BGM 중복으로 계산하지 않았다.

| 검사 | 통과 그룹 |
| --- | --- |
| `tests/bgm_smoke.py`: 원문·음원 보존, 실제 BGM 7가지 요청 상황 | 9 |
| `tests/selection_smoke.py`: 원본 보호·JS 문법·선택·세 캐릭터·조작 | 15 |
| `tests/game_audit.py`: 전투·아이템·20개 웨이브·보스·N1 회귀 | 11 |
| `tests/trio_body.py`: 기존 이미지·방향·크기·발사·축·피격 경계 | 8 |
| `tests/exit_dialog.py`: 종료 모달·네이티브 전체화면 유지 | 10 |
| `tests/galaxy_standalone.py`: 최신 HTML 오프라인과 BGM 게임 오버/재시작 | 15 |

총 **68개 검사 그룹 통과**. N1은 해결됐고 N2(다음 단계에서 보스 보상 소실)는 기존 상태로 유지했다. 잡히지 않은 JS 오류·기본 대화상자는 없었다.

```sh
python tests/bgm_smoke.py --artifacts /absolute/path/to/bgm-review
```

상세 결과: [BGM](test-results.json), [선택·게임](selection-regression.json), [전체 기능](game-audit.json), [기존 트리오](trio-regression.json), [종료창·전체화면](exit-regression.json), [독립 HTML](../galaxy-test/test-results.json).

![게임 오버 후 선택화면과 음악 ON 설정 유지](game-over-music-stopped.png)

이 스크린샷 자체가 무음을 증명하는 것은 아니며, 정지 여부는 위의 실제 오디오 상태·재생 시간 검사로 확인했다.

## 최신 갤럭시 파일과 검증 한계

HTML과 ZIP을 다시 만들고 압축 해제 후 바이트 일치·CRC·`unzip -t`, ZIP 안의 새 정지 코드 포함을 확인했다. [다운로드 안내](../galaxy-test/README.md) · [패키지 검증](package-verification.json).

- HTML: **28,098,804바이트**, SHA-256 `f15bfe3c42712ef9d71f179800d158502ba4926eef29425e52eb400cd49f78b4`
- ZIP: **20,314,990바이트**, SHA-256 `eb91c199b589220426afff7ea8546f2badf47b826188881908bc32d70545803a`

실제 스피커 청취는 하지 않았다. 따라서 실제 음량·음질·지연·짧은 잡음·블루투스 출력·앱 복귀 소리는 미검증이다. 실제 Galaxy Samsung Internet/Chrome·센서·Android 시스템 UI·로컬 파일 연결·성능도 기기에서 확인해야 한다.

이 환경은 관리자 정책으로 `file://` 열기를 차단하므로 독립 HTML을 동일한 새 문서에 주입해 오프라인으로 검사했다. 정책을 우회하지 않았다. 체력·보스·지역 전환은 상태 설정 검사이며 사람이 난도 그대로 전 지역을 완주한 것은 아니다.

최신 트리오 시안 적용은 별도 미완료 작업이다. 이번 커밋은 BGM 수정·검사·기록·갤럭시 패키지만 포함하며 `main` 병합·GitHub Pages 배포는 하지 않는다.
