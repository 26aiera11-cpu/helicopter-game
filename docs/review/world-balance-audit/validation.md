# 검증 결과 및 한계

2026-11-08 KST · Chromium154.0.8037.57 · 기준 `07c3d34331770f53817ca513241949ec19fe8dbe`. 등록84개 중 관련35개 실행, 최종35개 통과·실패0개, 완료 516그룹. 미실행49개는 아래에 별도 기재한다. 자동 검사를 사람의 체감 난이도 승인으로 해석하지 않는다.

## 회귀 결과

| 검사 | 완료 그룹 | 실제 로그 |
|---|---|---|
| world_balance_labels-native | 5 | [결과](tests/world_balance_labels-native/test-results.json) · [로그](tests/world_balance_labels-native/run.log) |
| world_balance_labels-offline | 5 | [결과](tests/world_balance_labels-offline/test-results.json) · [로그](tests/world_balance_labels-offline/run.log) |
| worlds | 20 | [결과](tests/worlds/test-results.json) · [로그](tests/worlds/run.log) |
| worlds-offline | 19 | [결과](tests/worlds-offline/test-results.json) · [로그](tests/worlds-offline/run.log) |
| default_world_route-native | 10 | [결과](tests/default_world_route-native/test-results.json) · [로그](tests/default_world_route-native/run.log) |
| default_world_route-offline | 10 | [결과](tests/default_world_route-offline/test-results.json) · [로그](tests/default_world_route-offline/run.log) |
| scoring | 17 | [결과](tests/scoring/test-results.json) · [로그](tests/scoring/run.log) |
| scoring-offline | 17 | [결과](tests/scoring-offline/test-results.json) · [로그](tests/scoring-offline/run.log) |
| mobile_controls | 23 | [결과](tests/mobile_controls/test-results.json) · [로그](tests/mobile_controls/run.log) |
| exit_dialog | 10 | [결과](tests/exit_dialog/test-results.json) · [로그](tests/exit_dialog/run.log) |
| fullscreen_smoke | 7 | [결과](tests/fullscreen_smoke/test-results.json) · [로그](tests/fullscreen_smoke/run.log) |
| selection_smoke | 15 | [결과](tests/selection_smoke/test-results.json) · [로그](tests/selection_smoke/run.log) |
| game_over | 7 | [결과](tests/game_over/test-results.json) · [로그](tests/game_over/run.log) |
| developer_start-native | 18 | [결과](tests/developer_start-native/test-results.json) · [로그](tests/developer_start-native/run.log) |
| developer_start-offline | 18 | [결과](tests/developer_start-offline/test-results.json) · [로그](tests/developer_start-offline/run.log) |
| machine_boss-native | 26 | [결과](tests/machine_boss-native/test-results.json) · [로그](tests/machine_boss-native/run.log) |
| machine_fortress_bgm-native | 22 | [결과](tests/machine_fortress_bgm-native/test-results.json) · [로그](tests/machine_fortress_bgm-native/run.log) |
| machine_normal-native | 22 | [결과](tests/machine_normal-native/test-results.json) · [로그](tests/machine_normal-native/run.log) |
| machine_fortress-native | 13 | [결과](tests/machine_fortress-native/test-results.json) · [로그](tests/machine_fortress-native/run.log) |
| storm_sky-native | 19 | [결과](tests/storm_sky-native/test-results.json) · [로그](tests/storm_sky-native/run.log) |
| storm_sky_bgm-native | 19 | [결과](tests/storm_sky_bgm-native/test-results.json) · [로그](tests/storm_sky_bgm-native/run.log) |
| volcano_boss-native | 16 | [결과](tests/volcano_boss-native/test-results.json) · [로그](tests/volcano_boss-native/run.log) |
| volcano_combat-native | 14 | [결과](tests/volcano_combat-native/test-results.json) · [로그](tests/volcano_combat-native/run.log) |
| volcano_mixed-native | 13 | [결과](tests/volcano_mixed-native/test-results.json) · [로그](tests/volcano_mixed-native/run.log) |
| snowfield_boss-native | 19 | [결과](tests/snowfield_boss-native/test-results.json) · [로그](tests/snowfield_boss-native/run.log) |
| snowfield_combat-native | 16 | [결과](tests/snowfield_combat-native/test-results.json) · [로그](tests/snowfield_combat-native/run.log) |
| snowfield_difficulty-native | 9 | [결과](tests/snowfield_difficulty-native/test-results.json) · [로그](tests/snowfield_difficulty-native/run.log) |
| selection_bgm | 14 | [결과](tests/selection_bgm/test-results.json) · [로그](tests/selection_bgm/run.log) |
| selection_bgm-offline | 14 | [결과](tests/selection_bgm-offline/test-results.json) · [로그](tests/selection_bgm-offline/run.log) |
| item_persistence | 7 | [결과](tests/item_persistence/test-results.json) · [로그](tests/item_persistence/run.log) |
| item_spawn_rules | 19 | [결과](tests/item_spawn_rules/test-results.json) · [로그](tests/item_spawn_rules/run.log) |
| boss_reward | 8 | [결과](tests/boss_reward/test-results.json) · [로그](tests/boss_reward/run.log) |
| galaxy_standalone | 19 | [결과](tests/galaxy_standalone/test-results.json) · [로그](tests/galaxy_standalone/run.log) |
| multitouch_exit-native | 13 | [결과](tests/multitouch_exit-native/test-results.json) · [로그](tests/multitouch_exit-native/run.log) |
| multitouch_exit-offline | 13 | [결과](tests/multitouch_exit-offline/test-results.json) · [로그](tests/multitouch_exit-offline/run.log) |

## 실패 이력과 검사 보완

최초33개 모음 중8개가 실패했다.6개 기계요새·폭풍 검사는 원본 바이트 보호에서 score.js의 승인된 UI 차분을 역변환하지 못해 전투 실행 전에 실패했다. 각 보호 검사에19개 정확한 허용 차분의 역변환 경로를 연결했다. 원본 Git 소스·아틀라스·음원 해시·AI·숫자 단언은 그대로 유지했고, 허용 차분을 광범위한 정규식이나 skip으로 바꾸지 않았다.

설원 일반/보스2개는 이전의 기본20단계/OFF를 기대해 실패했다. 현재 승인된 기본40을 바꾸지 않고, 이 역사적20단계 비교 검사만 보존된 OFF 옵션을 명시 선택하게 했다. 기본40은 별도의 native/offline10그룹과 실제40단계9표본에서 확인한다. 최초 실패 원본 로그·당시 전체 검사 소스 압축·차분을 attempts에 보존하고, 해당8개만 재검사했다. 최신 #30 전용 native/offline2개를 추가 실행했다. 최종 결과는 통과한 검사마다 한 번만 합산하며 실패 전 부분 그룹은 합산하지 않았다.

재검사 중 기계요새 그래픽 모음은12부분 그룹 뒤 미사용 volcano_boss.wav의 requestfailed를 관측했다. 원래 로그는 실패 이유 문자열을 담지 않아 정확한 브라우저 취소 원인까지 단정하지 않는다. 빠른 재시작 전에 모든 원래 음원의 buffered가 끝까지 도달하도록 준비 대기를 보강했고, 요청 실패 단언을 유지한 후 해당 모음만 다시 통과했다. WAV/재생 코드/경로는 수정하지 않았다. [원본 실패](attempts/rerun-resource-failure/machine_fortress-native/run.log)와 [당시 검사](attempts/machine-fortress-before-preload.py)를 보존했다.

[첫 검사 전체 시도](attempts/initial-suite-results.json) · [재검사/추가 검사](attempts/rerun-suite-results.json) · [최초 검사 소스](attempts/initial-test-sources.tar.gz) · [최초 후보 차분](attempts/initial-candidate.diff). 환경 초기화 이전에 잃은 로그는 이 자료와 구분하며 [recovery.md](recovery.md)에 요약한다.

## 새 화면·기록·자산 보호

일반/오프라인 각각4지역×1·5단계×3가로 화면(915×412,800×360,568×320), 도움말·순위표·최종클리어를 검사했다. DOM 실제 표시와 Canvas.fillText를 관찰하여 `(시험)` 미노출, 정상 모드 개발 배너 숨김, 개발자 직접시작 기능과 정확한 BGM 안내를 확인했다. 새 결과 저장 전후에도 과거 알려진 기록 필드와4개 저장소 키를 보존한다.20/40기록을 병합하거나 마이그레이션하지 않았다.

소스 보호는 index.html 전체와128자산의 실제 바이트 일치,3개 표시 자산의19개 정확 차분 역변환을 확인한다. 멀티터치 후 나가기의 실제 신뢰된 입력과 click 누락 주입, 취소/확정/재열기/키보드·마우스·전체화면을 검사했다. 조작·전투·생성·무기·보상·음악 수치는 바꾸지 않았다.

선택 MP3와 단계/보스 WAV는 HTMLMediaElement의 paused/currentTime 및 전환·중복 재생 상태로 확인한다. 스피커 음질·반복 접합의 음악적 자연스러움은 직접 청취와 구분한다. 모든 이미지는 원본을 유지한다.

## 측정·패키지

9개 자연40단계,144개 정지 표적,480개 보스,432개 일반1단계 조건을 재실행했다. 보스479처치/1사망, 일반430완료/2사망을 실패 포함 CSV에 공개했다. 완벽한 좌표 정보와 즉시 반응 봇이며, 강제 무적/즉사/부활은 사용하지 않는다. 이것은 사람의 승률이 아니다. 설정상 가동률·연속 이동 근사·이항 분포는 실측과 구분했다.

[패키지](package.json), [독립 압축해제·전체 바이트/원본 리소스·27스크립트 문법](standalone-integrity.json)과 galaxy_standalone에서 최신 정확HTML, 단일엔트리ZIP/CRC/별도 압축해제, 오프라인 외부요청0을 확인했다. 관리 환경의 file:// 탐색 제한은 우회하지 않았다. 실제 갤럭시 삼성 인터넷/Chrome의 파일 연결·물리 센서·스피커·체감 회피 난이도는 미검증이다. 복구 후 cgroup의 OOM/oom_kill은0으로 증가하지 않았다.

## 이번에 실행하지 않은49개 모음

중복 오프라인 변형·과거 그래픽 제작·이전 밸런스 대조 등은 이번 관련35개 회귀와 소스 보존 검사로 범위를 정했다. 아래 검사를 실행한 것처럼 합산하지 않았다.

`snowfield_mixed-native`, `snowfield_art`, `snowfield_mixed-offline`, `game_audit`, `snowfield_art-offline`, `item_monsters`, `item_spawn_rules-offline`, `item_monsters-offline`, `tanko_cadence`, `tanko_combat`, `tanko_combat-offline`, `bgm_smoke`, `joystick_design`, `mobile_controls-offline`, `joystick_design-offline`, `snowfield_combat-offline`, `snowfield_difficulty-offline`, `ppyoko_title-native`, `snowfield_boss-offline`, `volcano_lifecycle`, `volcano_fallback`, `volcano_package`, `ppyoko_title-offline`, `volcano_art-native`, `volcano_art-offline`, `volcano_visual_fix-native`, `volcano_visual_fix-offline`, `volcano_combat-offline`, `volcano_boss-offline`, `volcano_boss_masks`, `volcano_breath_art-native`, `volcano_breath_art-offline`, `volcano_mixed-offline`, `volcano_bgm-native`, `volcano_bgm-offline`, `storm_sky-offline`, `storm_sky_edges`, `storm_background_fit-native`, `storm_background_fit-offline`, `storm_background_integrity`, `storm_sky_bgm-offline`, `machine_fortress-offline`, `machine_normal-offline`, `machine_background_dash-native`, `machine_background_dash-offline`, `machine_cover-native`, `machine_cover-offline`, `machine_boss-offline`, `machine_fortress_bgm-offline`

main 병합·Pages 배포·수치 조정은 하지 않는다. 보고서 권장안은 사용자 검토 후 별도 작업으로 결정한다.
