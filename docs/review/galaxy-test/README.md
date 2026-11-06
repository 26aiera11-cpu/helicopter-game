# 갤럭시 테스트 — 화산 전용 BGM 2곡 1차 시험

2026-11-06 KST · `feature/volcano-bgm` · [Issue #23](https://github.com/26aiera11-cpu/helicopter-game/issues/23)

**[최신 갤럭시 ZIP 다운로드 — 약46.6MB](https://github.com/26aiera11-cpu/helicopter-game/raw/refs/heads/feature/volcano-bgm/dist/heli_trio_galaxy_test.zip?download=1)**

ZIP은 **46,561,162바이트**, 안에는 `heli_trio_galaxy_test.html` 하나만 있다. HTML은 **63,951,624바이트**다. 두 신규WAV·기존 음원·이미지/CSS/17스크립트를 포함해 외부 파일이 필요 없다.

1. 갤럭시에서 ZIP을 받아 ‘내 파일→다운로드’에서 압축을 푼다. HTML을 로컬 파일 실행이 가능한 브라우저로 연다. Android 파일 연결/로컬 실행 지원은 실제 기기에서 확인해야 한다.
2. 가로 화면에서 음악을ON으로 두고 캐릭터를 터치한다. 첫 사용자 동작 이후에만 선택 BGM을 시도한다. 거부되면 다음 터치에서 재시도하며 브라우저 보안 정책을 우회하지 않는다.
3. 상단 전체화면 버튼을 사용한다. 브라우저가 거부해도 일반 화면에서 동작한다. 선택→게임→내부 나가기 확인창→선택 복귀 중 전체화면을 유지한다.
4. **게임 방법→🧪 지역 바로 시작→월드2→화산→1~5단계**를 선택하고 도움말을 닫아 시작한다. 1~4는 혼합 일반전·전용 일반 BGM, 직접5는 즉시 드래곤·전용 보스 BGM이다. 개발 테스트 기록은 저장하지 않는다.
5. 정상 월드2 시험은 기본OFF다. 켜면 숲→바위→바다→사막→설원→화산30단계를 플레이하고 별도 시험 기록에 저장한다. 기본OFF는 기존 월드1 20단계다. 정상 화산5는 혼합 일반 몬스터6마리 처치 후 보스다.

## 음악 직접 듣기·실기기 확인

- [화산 일반곡 WAV](https://github.com/26aiera11-cpu/helicopter-game/raw/refs/heads/feature/volcano-bgm/assets/audio/volcano_stage.wav?download=1) —136BPM/E단조/16마디/약28.24초.
- [마그마 드래곤 보스곡 WAV](https://github.com/26aiera11-cpu/helicopter-game/raw/refs/heads/feature/volcano-bgm/assets/audio/volcano_boss.wav?download=1) —114BPM/C단조/16마디/약33.68초.
- **사용자 청취 승인 전인1차 시험용**이다. 실제 휴대폰에서 저음/음량·반복 접점·효과음 가청성을 확인한 후 피드백을 받는다.
- 일반→보스에서 한 곡만 재생되는지, 음악OFF/ON과 별도 효과음 설정, 나가기 취소/확정, 게임 오버3초 무음→선택곡 복귀, 화면잠금/백그라운드 후 복귀를 확인한다.
- 숲·바위·바다·사막과 선택 MP3는 원본이고, 설원만 숲 임시 BGM을 계속 사용한다.

캐릭터/무기·혼합 확률·아이템/점수/저장·승인된 드래곤 아래0.2초 선분사 후3.8초360° 브레스, 자이로 주 이동/드래그 보조·조이스틱30/22px·8% 데드존·멀티터치·내부 종료·전체화면 기능을 유지했다.

**58개 모음 중57개 통과·1개 실패, 완료 그룹724개.** 실패는 기존 설원 장기멀티터치 후 나가기 검사다. 변경 없는 재검사와 새 BGM 이전 기준에서도 재현되어 미해결로 남긴다. 두 곡의 PCM형식/재생성·샘플 접점/무음/클리핑, 일반·오프라인 실제play/pause/currentTime 증가·최대1곡, ZIP1항목·CRC·별도 추출·소스/오디오 바이트 일치를 확인했다.

- [전체 결과·곡 구성·변경 파일·화면·한계](../volcano-bgm/README.md)
- [빌드 정보](build-results.json) · [ZIP 정보](zip-results.json) · [독립HTML 검사](test-results.json)
- HTML SHA256 `c67f2077e0a9dc87d203fb446b3e44b6472806b433b7bfcb553ce5dc424a184f`
- ZIP SHA256 `867c8c9de4d5d142492aeaedaa5fe883cf09118fbfe1481829cfc5554d887003`

![화산 보스전](../volcano-bgm/focused/volcano_bgm-native/volcano-bgm-phase5-568x320.png)

화면/미디어 검사는 실제 Chromium이며 물리 갤럭시나 스피커 청취 결과가 아니다. 관리 환경의file:// 보안 정책을 우회하지 않고 빈localhost origin에 같은HTML을 넣고 네트워크를 차단했다. 기기별 최초 재생/저장/파일 연결·센서/손가락 조작·음향/발열/성능을 확인해야 한다. 이전부터 기록된 긴멀티터치→나가기 간헐 현상이 이번 설원5단계 전체 회귀에서도 재현됐다. 변경 없는 단독 재실행과 BGM 이전 기준에서도 재현됐으며 원인은 확정하지 못했다. 실제 갤럭시에서 반복 확인이 필요하다. [당시 입력 진단](../volcano-bgm/regression/worlds/exit-touch-failure.json)을 남기며 근본 해결을 주장하지 않는다.

로컬 순위는 브라우저/주소별로 저장하며 기기/Pages/로컬 파일 사이에 자동 공유되지 않는다. 기존 기록은 삭제/환산하지 않았다. **main 병합과 GitHub Pages 배포는 하지 않는다.**
