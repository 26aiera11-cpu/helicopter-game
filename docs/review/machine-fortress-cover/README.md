# 기계 요새 배경 단일 Cover — Issue #35

[Issue #35](https://github.com/26aiera11-cpu/helicopter-game/issues/35)의 최신 본문과 댓글1개를 먼저 확인했다. 사용자가 탄환 변경을 취소했으므로 **이번 범위는 배경뿐**이다. 브랜치 이름에 `projectiles`가 남아 있지만 발사체 기능/추가 E2E 진단은 진행하지 않는다. 기준 SHA는 `46e86319a3924bfd0ef68cb9627bef5041f354fc`, 이미 생성된 작업 브랜치는 `fix/machine-fortress-cover-projectiles`다. main 병합·GitHub Pages 배포 없이 이 브랜치에만 커밋·푸시한다.

## 실제 게임 코드 변경

**`assets/machine_fortress/machine_fortress.js` 한 파일만 수정했다.** `extendedBackground()`와 흐림·어두운 overlay·오프스크린 보조 Canvas·배경 캐시·contain+cover 이중 표시를 제거했다. 설원/화산의 `backgroundGeometry()`와 같은 아래 계산으로 원본을 한 번 그린다.

```js
const scale=Math.max(w/image.naturalWidth,h/image.naturalHeight);
const width=image.naturalWidth*scale,height=image.naturalHeight*scale;
ctx.drawImage(image,(w-width)/2,(h-height)/2,width,height);
```

이미지가 로드되기 전 기존 기본색 fallback만 유지한다. 로드된 원본 RGB 이미지가 화면을 덮으므로 어두운 overlay나 보조 이미지가 겹치지 않는다. 원본 비율·중앙 정렬을 유지하며 화면 비율에 따른 가장자리 잘림은 사용자 승인된 Cover 동작이다.

| 화면(CSS px) | Cover 표시 크기 | 화면 밖으로 잘리는 양(CSS px) |
| --- | --- | --- |
| 915×412 | 약915×514.96 | 위/아래 각각약51.48 |
| 800×360 | 약800×450.24 | 위/아래 각각약45.12 |
| 568×320 | 약568.59×320 | 좌/우 각각약0.29 |

원본은1672×941 PNG이며 SHA256 `89990eeac3ae96c8ed5c2d9af2d90a5f3d8e51e95ccecf3757db1f9e21f9f124` 그대로다. PNG를 잘라 저장하거나 비율을 변형하지 않았다. 게임 화면이 원본 전체를 보여야 한다는 이전 contain 조건은 이번 Cover 요구로 대체됐다.

## 보호한 기능

[정확한 보존 검사](preservation.json)는 기존128자산 중 **127개와 index.html이 원본 바이트를 유지**함을 확인한다. 변경한 렌더러도 배경 부분2차분만 역변환하면 기준 전체 파일과 같다. 과거 해시를 새 값으로 덮어쓰지 않았다.

- `config.js`, `spawns.js`, `combat.js`와 index의 공격/피해/탄환/레이저/발사·충돌 코드는 변경하지 않았다. 기존 나사봇·톱니벌은 돌진 전용, 드론은 레이저, 포탑은 주황 포탄이라는 역할을 유지한다.
- 나사봇H×.40/100px/s, 톱니벌H×.70/145px/s, 동적 시간·예고/쿨다운/경계 제한·HP·등장 확률을 유지한다.
- 일반40px/기가코어132px·애니메이션·PNG11개·원본 manifest·모든 음원·다른 지역·플레이어/무기·아이템·점수/저장·조작/센서/전체화면/종료 확인창을 유지한다. 기가코어 특수 공격/폭주 강화/전용 음악도 이번에 구현하지 않는다.

## 검증

**등록74모음 중 관련10개를 실행해 모두 통과·완료144그룹**이다. 신규 Cover8/7그룹, 기존 배경/돌진12/11그룹, 그래픽/보스13/13그룹, 기존 전투22그룹, worlds20그룹, 독립HTML19그룹, 폭풍 하늘19그룹이 통과했다. 모음별 집계와 원문은 [test-summary.json](test-summary.json) 및 `tests/` 아래에 기록한다. 전체74모음 재실행은 아니다.

- 신규 Cover 검사는 일반8/오프라인7그룹이다.915×412/800×360/568×320/1672×941/412×915 및DPR1/2의10조건에서 한 번의 원본 drawImage·filter none·alpha1을 확인했다. 전체 Canvas 픽셀이 별도 Cover 참조와 차이0·알파255였고 이미지 잘림 범위도 수치로 남겼다.
- 실제 게임1~5단계에서 같은 원본/표시 좌표를 사용하며 개발자5단계는 기존20HP 기가코어로 즉시 시작했다. 세 가로 화면 모두 실제DPR2 문맥에서도 확인하고 세로→가로 리사이즈·HUD/조이스틱/발사/전체화면/나가기 배치를 검사했다.
- 기존 배경/돌진 검사의 기대치만 새 Cover로 바꿨다. 폐기된 블러/캐시 기대값은 이미지 한 번·추가 Canvas 생성0·filter 접근 불필요·전체 Cover 픽셀 일치로 대체했고, 기존48돌진 경로·속도·예고/끝점·쿨다운 검사는 그대로 유지했다. 그래픽/보스 검사도 배경의 min→max 기대값만 바꿨다.
- 기존 기계 요새 네 역할/보스·다른 지역·월드 진행·독립HTML 자동 검사를 회귀 수준으로 실행한다. 탄환 기능을 추가하거나 기존 실패를 제거하는 변경은 없다.

기존 **Issue #30 설원 긴3점 멀티터치 후 나가기 click 누락**은 이번 worlds20그룹에서는 재현되지 않았다. 낮은 우선순위의 별도 미해결로 유지하며 조작 코드도 변경하지 않았다. 이번 통과를 해결 근거로 삼지 않고 [과거 실패 기록](../machine-fortress-background-dash-range/tests/worlds/exit-touch-failure.json)도 보존한다.

실물 Galaxy Samsung Internet/Chrome의 최종 그래픽·센서·멀티터치·장시간 성능·로컬 파일 연결은 미검증이다. 제어 입력/시간을 사용한 실제 headless Chromium 검사를 실물 승인으로 표현하지 않는다. 관리 환경의 file:// 제한을 우회하지 않고 네트워크를 끈 빈 origin에 동일 HTML을 주입해 오프라인 실행을 확인한다.

## 실제 전후 화면

| 화면 | 이전 흐림 확장 | 단일 Cover |
| --- | --- | --- |
| 915×412 | [이전](tests/machine_cover-native/before-comparison-915x412.png) | [수정 후](tests/machine_cover-native/after-comparison-915x412.png) |
| 568×320 | [이전](tests/machine_cover-native/before-comparison-568x320.png) | [수정 후](tests/machine_cover-native/after-comparison-568x320.png) |

[800×360](tests/machine_cover-native/after-800x360.png) · [실제DPR2 보스 화면](tests/machine_cover-native/after-boss-568x320-dpr2.png).

기준46e8631의 렌더러만 별도 URL에 그대로 제공하고 현재 렌더러와 비교했다. 캐릭터·종류·좌표·프레임·PNG·전투 코드는 같고 배경만 다르다. 이미지 합성/수작업 편집이 아닌 실제 게임 Canvas 캡처다.

## 갤럭시 테스트 파일

[단일 HTML](../../../dist/heli_trio_galaxy_test.html)은 **76,795,609바이트**, SHA256 `f107252127ddc4337609da5806f4b053d1d06959fd548834d4f7e7816c2d4938`이다. ZIP은 **56,141,225바이트(약53.54MiB)**, SHA256 `1318c100174bdd94e1e5a7257d5624522cbfb265cc83d43ff7101e94191863c9`다.

- [갤럭시 ZIP 다운로드](https://raw.githubusercontent.com/26aiera11-cpu/helicopter-game/refs/heads/fix/machine-fortress-cover-projectiles/dist/heli_trio_galaxy_test.zip)
- [빌드](build.json) · [ZIP CRC/크기](package.json) · [별도 압축해제/내장 원본 검사](embedded-verification.json)

기존 빌드/패키지 스크립트는 수정하지 않고 현재 소스를 재생성했다. ZIP은 최신 HTML 한 개만 포함한다. 별도 압축해제 후 전체 바이트 일치/CRC·26스크립트와 현재 기계 요새4모듈·PNG11개·기존 외부음원5파일·원본 manifest·복구 Storm 배경 내장을 확인했다. 기계 요새 인라인 렌더러에서 흐림/확장 코드가 사라지고 단일 Math.max Cover가 포함된 것도 확인했다. 원격 ZIP 직접 다운로드 검증과 최종 커밋 SHA는 작업 완료 보고에 함께 기록하며 [지정 브랜치 커밋 내역](https://github.com/26aiera11-cpu/helicopter-game/commits/fix/machine-fortress-cover-projectiles)에서도 확인할 수 있다.

보고서 JSON에 큰 data URI가 있으면 공개 사본에서 MIME/길이/SHA256 설명으로 치환한다. 상태·수치·실패는 보존하고 원본·사본 해시를 `artifact-manifest.json`에 기록한다. 실제 게임 자산/ZIP/HTML은 이 과정에서 수정하지 않는다. main 병합과 GitHub Pages 배포는 하지 않는다.
