# 선택화면 전용 BGM 적용·검증

2026-11-02(KST) · `feature/selection-screen-integration` · 기준 `dcd2fe20ced91447a5410e27f5929e421712f6c5`

사용자가 첨부한 `heli_trio_selection_bgm_track2.mp3`를 [음원 자산](../../../assets/audio/heli_trio_selection_bgm_track2.mp3)으로 그대로 사용했다. 원본은 **990,740바이트**, SHA-256은 `ca7e760a474db29eed29f0e0f6e34406d0415f0143aa3075953e98096ff8ba53`이다. 첨부 파일·저장소 자산·독립 HTML에서 디코딩한 MP3가 바이트 단위로 같다. 편집·트리밍·페이드·재인코딩이나 다른 음악 대체를 하지 않았다.

## 음악 제어

- 선택화면에 보이지 않는 `audio#selectionBgm` 하나를 두고 `loop`로 재사용한다. 첫 신뢰할 수 있는 터치·키보드 동작 전에는 `play()`를 호출하지 않는다. 캐릭터 선택을 바꿔도 같은 요소와 재생 시간이 유지된다.
- 선택화면 볼륨은 `0.34`, 기존 스테이지 볼륨은 `0.42`다. 읽기 전용 평균 레벨 측정에 볼륨을 적용하면 숲 음악보다 약 **0.6dB 낮다**. 이 값은 체감 음량에 대한 청취 검사를 대신하지 않는다.
- 게임 시작 시 메뉴 음악을 동기적으로 정지·되감은 뒤 기존 숲 음악을 시작한다. 단일 제어기가 선택/스테이지/보스 반복 음악 중 하나만 재생한다. 재생 중인 동일 곡을 매 프레임 다시 시작하지 않는다.
- 게임 오버 즉시 게임 음악을 정지한다. 기존 3초 GAME OVER 화면 동안 모든 BGM이 멈추고, 선택화면 복귀 후 선택 음악을 재생한다. 음악 OFF이면 복귀해도 무음이다.
- 기존 종료창의 취소는 게임 음악을 유지하고, 종료 확정·최종 클리어 후 선택화면 복귀는 선택 음악을 재생한다. 기존 전체화면·종료창·클리어 효과를 변경하지 않았다.
- 기존 음악 ON/OFF 버튼이 두 화면의 BGM을 함께 제어한다. 효과음 토글은 독립적으로 유지한다. 재생 거부를 처리하고 같은 요청을 프레임마다 반복하지 않으며, 다음 사용자 동작에서 같은 요소로 재시도한다. 브라우저 정책을 우회하지 않는다.
- 문서가 숨겨지면 음악을 정지하고 다시 보일 때 현재 상태의 곡을 시도한다. 비동기 `play()` 완료 시 화면이 바뀌었다면 해당 곡을 정지해 지연된 요청의 중복 재생을 방지한다.

게임 로직을 수정한 것이 아니라 `index.html`의 기존 최종 오디오 제어기와 숨김 음원 요소를 변경했다. 정확히 허용한 변경만 역변환하면 기준 커밋의 `index.html`과 같다. 기존 자산 파일 **10개**, 내장 이미지 URL **71개**, 기존 WAV **12개**와 선택 CSS/JS가 그대로임을 확인했다. 트리오·빙글·탱코, 탱코의 현재 피해·연사·관통/차단, 보스 HP/보상, 3초 게임 오버, 아이템 유지, UI·전체화면·종료 모달은 보호했다.

## 실행한 검사

| 검사 | 통과 그룹 | 결과 |
| --- | ---: | --- |
| 선택 BGM 일반 브라우저 | 14 | [실제 미디어 상태·시계·반복](browser/test-results.json) |
| 선택 BGM 독립 HTML 오프라인 | 14 | [외부 요청 없이 같은 전환 검사](offline/test-results.json) |
| 기존 게임 BGM 회귀 | 9 | [사망·ON/OFF·4지역/보스·재시작](game-bgm/test-results.json) |
| 갤럭시 독립 HTML 전체 | 19 | [자산·터치·전체화면·진행](../galaxy-test/test-results.json) |
| 전체 게임 진행 | 11 | [20웨이브·4보스 등](regression/game-audit.json) |
| 선택화면 | 15 | [선택 효과·애니메이션](regression/selection.json) |
| 내부 종료창 | 10 | [취소·확정·전체화면](regression/exit-dialog.json) |
| 게임 오버 | 7 | [3초 연출·깨끗한 복귀](regression/game-over.json) |
| 일반 아이템 유지 | 7 | [전환·수명·획득·초기화](regression/items.json) |
| 보스 보상 | 8 | [종류·확률·상한·중복·순서](regression/boss-reward.json) |
| 탱코 전투 일반/오프라인 | 14 + 14 | [일반](regression/tanko.json) / [오프라인](regression/tanko-offline.json) |
| 연사·최초 발사 회귀 | 5 | [강화별 간격·다른 캐릭터](regression/cadence.json) |

총 **147개 검사 그룹**이 통과했다. [집계 JSON](test-summary.json), [원본·패키지 무결성](package-verification.json)을 저장했다. 새 선택 BGM 검사는 실제 Chromium의 `play()`, `paused`, `currentTime`, 요소 수, 동기 호출/이벤트/프레임을 관찰한다. 자동 재생 거부 분기만 별도 문서에서 거부 Promise를 모의한 뒤 실제 터치로 네이티브 재생을 재시도했다.

첫 터치로 재생한 뒤 세 캐릭터를 바꿔도 음악이 유지됐다. 선택 BGM 전용 검사는 일반/오프라인 각각 **추가 12회 시작·복귀**를 확인했다. 네이티브 미디어 요소는 원래 WAV 12개+선택 MP3 1개의 **13개로 고정**, 반복 BGM 동시 재생은 **최대 1개**, 중복은 **0건**이었다. 별도 [첫 동작이 게임 시작인 검사](first-start.json)에서도 메뉴 곡이 잠깐 재생되지 않고 숲 곡만 시작했으며, 게임 오버 후 추가 터치 없이 메뉴 곡이 재생됐다.

915×412, 800×360, 568×320 가로 화면에서 캐릭터·기존 음악 버튼·전체화면·터치를 확인했다. 브라우저 기본 대화상자와 잡히지 않은 JS 오류가 없었다. Pages 프로젝트 경로와 같은 `/helicopter-game/` 아래에서 MP3 HTTP **206** 응답과 네이티브 재생을 검사했다. GitHub Pages에 배포하거나 배포된 신규 버전을 검사한 결과는 아니다.

## 반복 연결·음량의 확인 범위

브라우저가 인식한 길이는 **30.890917초**다. 일반 브라우저에서 처음부터 끝까지 자연스럽게 한 바퀴 재생하고, 끝부분으로 이동한 경우도 검사했다. 끝을 넘을 때 `paused=false`이고 재생 시간이 다시 증가했다. 오프라인에서도 실제 데이터 URL의 끝 경계를 검사했다.

루프 시작으로 시계가 돌아간 뒤 `currentTime > 0.03` 및 디코딩 가능 상태를 관찰하기까지 일반 약 **117ms**, 오프라인 약 **110ms**였다. 이는 프레임 표본으로 측정한 **시계 복구 관찰 시간**이며 스피커에서 무음이 난 시간과 같지 않다. 오프라인 경계 순간에는 일시적으로 `readyState=1`이 관찰됐다. 반복 후 시계가 정상 진행하는 것과 청감상 완전히 매끄러운 연결은 구분한다.

[원본 PCM 읽기 전용 분석](audio-analysis.json)에서 앞뒤의 -60dB 미만 연속 무음은 없지만, 마지막 100ms의 레벨이 첫 100ms보다 낮은 원본의 페이드가 확인됐다. 음악을 그대로 보존했으며, **실제 스피커에서 반복 연결이 자연스럽게 들리는지는 미검증**이다. 끊김을 없애기 위한 음원 가공은 하지 않았다.

## 배포·오프라인 패키지와 한계

[갤럭시 ZIP 다운로드·실행 안내](../galaxy-test/README.md). ZIP에는 외부 의존성이 없는 최신 HTML 한 개만 있다. HTML 안의 MP3가 첨부 원본과 같고, ZIP CRC·`unzip -t`·별도 실제 압축 해제 후 바이트 일치를 확인했다.

- HTML: **30,063,120바이트**, SHA-256 `ea54a175237534a52987cd24afd26483a3ade6347697e5cfe8d4574d999a190b`
- ZIP: **21,727,312바이트**, SHA-256 `b0cb735d2ef0472c9221ec7f321589d00ff9108e585e0cb7a46499bcbeda5f1b`
- 이 환경에서는 관리형 Chromium 정책이 직접 `file://` 접근을 차단한다. 정책을 변경하지 않고 동일 HTML을 새 빈 문서에 주입해 네트워크를 끈 상태로 검사했다. 직접 Android 로컬 파일 실행에 성공했다고 기록하지 않는다.
- 실제 Galaxy Samsung Internet/Chrome, Android 파일 연결·주소창/센서·앱 전환, 실기기 성능, 스피커 청취·체감 음량·음악의 반복 연결은 별도 확인이 필요하다.
- 기능 브랜치만 커밋·푸시한다. `main` 병합과 GitHub Pages 배포는 하지 않는다. 실제 Pages의 신규 버전 재생은 배포 후 별도 검증 대상이다.

## 재현 명령

```sh
python scripts/build_galaxy_test.py
python scripts/package_galaxy_test.py
python tests/selection_bgm.py --artifacts /tmp/heli-bgm-browser
python tests/selection_bgm.py --standalone --artifacts /tmp/heli-bgm-offline
python tests/bgm_smoke.py --artifacts /tmp/heli-game-bgm
python tests/galaxy_standalone.py --artifacts /tmp/heli-galaxy
```

![915×412 선택화면 — 시각적 UI 보존](browser/selection-music-915.png)

![568×320 오프라인 선택화면](offline/selection-music-568.png)
