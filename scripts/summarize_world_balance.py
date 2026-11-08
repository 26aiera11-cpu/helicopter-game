"""Rebuild the Korean Issue39 report from original-engine measurements (no tuning)."""
import csv,hashlib,json,math,statistics,subprocess
from pathlib import Path
from world_balance_harness import ROOT,BASE
OUT=ROOT/'docs/review/world-balance-audit';load=lambda n:json.loads((OUT/n).read_text());d=load('definitions.json');runs=load('route-samples.json');weapons=load('weapon-assays.json');bosses=load('boss-encounters.json');normals=load('normal-encounters.json');heroes=['뾰코','빙글','탱코']
assert len(runs)==9 and len(weapons)==144 and len(bosses)==480 and len(normals)==432
assert all(load('seed-replay.json').values());assert all(r['completed'] and r['deaths']==0 and len(r['phases'])==40 for r in runs)
def csvout(name,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fields);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
def fmt(v):return f'{v:.2f}' if isinstance(v,float) else str(v)
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','|'+'|'.join(['---']*len(head))+'|']+['| '+' | '.join(map(fmt,r))+' |' for r in rows])
def weight_label(row):
 if row['region']<4:return f"{len(row['weights'])}종 균등 · 각 {row['weights'][0]:.2f}%"
 return '/'.join(f'{x:g}' for x in row['weights'])
phase_rows=[];monster_rows=[]
for region in d['regions']:
 rid=region['id'];t=d['tactics'][rid]
 if rid<4:specs=[{'id':f'art-{i}','hp':1+region['combatProfile']//2,'speed':t['move'],'interval':t['interval'],'bullet':t['bullet']} for i in range(d['enemyArtCounts'][rid])]
 elif rid==4:specs=[{**p,'speed':38*p['move']*1.06,'interval':4.3*p['interval']*.95,'bullet':85*p['bullet']} for p in d['snowProfiles']]
 elif rid==5:specs=[{**p,'speed':38*p['move'],'interval':4.3*p['interval'],'bullet':85*p['bullet']} for p in d['volcanoProfiles']]
 else:specs=d['storm' if rid==6 else 'machine']['monsters']
 for spec in specs:monster_rows.append({'region':rid,'region_name':region['name'],**spec,'damage':1})
 for step in range(1,6):
  weight=[100/len(specs)]*len(specs) if rid<4 else d['difficulty'][region['key']]['spawnWeights'][step-1] if rid in [4,5] else d['storm' if rid==6 else 'machine']['weights'][step-1]
  interval=d['storm']['spawnIntervals'][step-1] if rid==6 else max(.72,t['spawn']-(step-1)*.09);cap=d['storm']['spawnCaps'][step-1] if rid==6 else min(7,3+region['combatProfile']+step//2)
  observations=[p for r in runs for p in r['phases'] if p['region']==rid and p['phase']==step]
  phase_rows.append({'region':rid,'name':region['name'],'phase':step,'weights':weight,'weighted_HP':sum(w*s['hp']/100 for w,s in zip(weight,specs)),'attempt_interval':interval,'admission_probability':.78,'uncapped_expected_interval':interval/.78,'enemies_plus_warnings_cap':cap,'required_kills':6,'spawn_warning':1.4,'median_seconds':statistics.median(x['seconds'] for x in observations),'min_seconds':min(x['seconds'] for x in observations),'max_seconds':max(x['seconds'] for x in observations),'median_peak_enemies':statistics.median(x['maxEnemies'] for x in observations),'median_peak_bullets':statistics.median(x['maxEnemyBullets'] for x in observations)})
progress=[]
for r in runs:
 entry=next(b for b in r['boundaries'] if b['to']==4);rec=r['result']['record'];assert rec['score']==100*rec['normalKills']+200*rec['itemKills']+32000
 progress.append({'hero':heroes[r['hero']],'seed':r['seed'],'policy':r['policy'],'seconds':r['seconds'],'snow_upgrade':entry['upgrade'],'snow_HP':entry['hp'],'normal_kills':rec['normalKills'],'item_kills':rec['itemKills'],'score':rec['score'],'damage':r['totals']['damage'],'blocked':r['totals']['blocked'],'final_upgrade':r['upgrade']})
models=[]
for quota in [3,2]:
 for collect in [0,.5,1]:
  dist=[0.0]*6;n=quota*4;q=.5*collect
  for k in range(5):
   for j in range(n+1):dist[min(5,k+j)]+=math.comb(4,k)/16*math.comb(n,j)*q**j*(1-q)**(n-j)
  models.append({'quota':quota,'assumed_collection_rate':collect,'capped_upgrade_distribution':dist,'mean_upgrade':sum(i*p for i,p in enumerate(dist)),'probability_level5':dist[5]})
corridors=[]
for height in [320,360,412]:
 for h,profile in enumerate(d['flightProfiles']):
  vmax=profile['accel']/profile['drag'];cap=d['playerSpeed'][h];t=1.2;tcap=-math.log(1-cap/vmax)/profile['drag'] if cap<vmax else math.inf;s=min(t,tcap);distance=vmax*(s-(1-math.exp(-profile['drag']*s))/profile['drag'])+cap*max(0,t-tcap)
  corridors.append({'height':height,'hero':heroes[h],'safe_band':height*.25,'usable_center_band':height*.25-24,'nominal_speed_cap':cap,'unit_axis_terminal_speed':min(cap,vmax),'warning_time':t,'distance_from_rest_in_warning':distance,'worst_opposite_edge_to_safe_center':height*.75})
source_names=['index.html','assets/worlds/worlds.js','assets/worlds/difficulty.js','assets/score/score.js','assets/controls/controls.js','assets/item_monster/item_monster.js']+[str(p.relative_to(ROOT)) for region in ['snowfield','volcano','storm_sky','machine_fortress'] for p in (ROOT/'assets'/region).glob('*.js')]
metrics={'baseline':BASE,'scope':'Numeric engine unchanged; measurements use the clean-label UI candidate. Removing the normal notice can affect existing UI-aware hazard placement.','source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(set(source_names))},'definitions':d,'phases':phase_rows,'monsters':monster_rows,'progression':progress,'item_models':models,'safe_corridors':corridors,'method':{'natural_40_stage_runs':9,'seeds':[202611081,202611082,202611083],'policies':['ignore (incidental hits/pickups still possible)','opportunistic','collect'],'physics_hz':60,'weapon_assays':144,'weapon_assay_hz':[60,120],'boss_encounters':480,'normal_phase1_encounters':432,'normal_counterfactual_new_item_opportunities':0,'standardized_first_fire_cooldown':0,'diagnostic_effects_output_suppressed':True,'boss_spawn_defeat_observation_resolution_seconds':1/60,'forced_invulnerability':False,'instant_kills':False,'revival':False,'human_evidence':False,'bot':'Known enemy/hazard positions, zero reaction latency, normalized virtual sensor input and original joystick keyboard max-turn handler; original movement/attack/collision/health/reward code active. Main render RAF paused only. Fresh browser context; no personal records.'}}
(OUT/'baseline-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
csvout('phase-metrics.csv',phase_rows);csvout('monster-profiles.csv',monster_rows);csvout('progression.csv',progress);csvout('weapon-assays.csv',weapons);csvout('safe-corridors.csv',corridors)
csvout('boss-times.csv',[{'hero':heroes[x['hero']],**x['encounter'],'seconds':x['seconds'],'defeated':x['encounterDefeated'],'damage':x['totals']['damage'],'blocked':x['totals']['blocked']} for x in bosses])
csvout('normal-phase-times.csv',[{'hero':heroes[x['hero']],**x['scenario'],'seconds':x['seconds'],'cleared':x['cleared'],'damage':x['damage_received'],'actual_normal_kills':x['result']['record']['normalKills']} for x in normals])
regional=[]
for run in runs:
 for region in range(8):
  ps=[x for x in run['phases'] if x['region']==region];b=next(x for x in run['bosses'] if x['region']==region)
  elapsed=sum(x['seconds'] for x in ps)
  regional.append({'hero':heroes[run['hero']],'seed':run['seed'],'policy':run['policy'],'region':region,'name':d['regions'][region]['name'],'entry_upgrade':ps[0]['entryUpgrade'],'entry_HP':ps[0]['entryHP'],'total_seconds':elapsed,'boss_seconds':b['bossSeconds'],'boss_spawn_HP':b['startHP'],'boss_spawn_upgrade':b['upgrade'],'to_boss_seconds':b['spawnTime']-ps[0]['time'],'post_boss_seconds':ps[-1]['time']+ps[-1]['seconds']-b['defeatTime'],'peak_enemies':max(x['maxEnemies'] for x in ps),'peak_enemy_bullets':max(x['maxEnemyBullets'] for x in ps)})
csvout('regional-progression.csv',regional)
lines=['# 월드1·2 전체 밸런스 분석 및 월드2 표시 정리','',f'기준 `{BASE}` · 작업 브랜치 `feature/world-balance-audit-clean-labels` · 2026-11-08 KST. [Issue #39](https://github.com/26aiera11-cpu/helicopter-game/issues/39), [백로그 #12](https://github.com/26aiera11-cpu/helicopter-game/issues/12).','',
'## 우선 검토할 5개 후보','',
'아래 수치는 후속 비교 실험을 위한 제안이다. **이번에는 전투·생성·보상·이동 수치를 하나도 변경하지 않았다.** 각 옵션은 별도 사용자 검토 대상이며, 함께 적용하면 영향이 중첩된다.','',
table(['우선순위','근거','다음 시험 범위','예상 영향과 위험'],[
[1,'사막 보스 기본HP65에서 월드2 보스는 모두20으로69.2% 감소. 강화 누적 상태에서 패턴 시작 전에 처치 가능.','설원72–80, 화산80–90, 폭풍90–105, 기가코어100–120의 기본HP 대조 실험.','현재 월드2 대비3.6–6배HP. 정지DPS를 가정하면 시간이 크게 늘어남. 탱코 장기전과 저강화 부담을 먼저 확인해야 함. 체감 난이도 비율로 직접 환산할 수 없음.'],
[2,'3→5강 보스HP는1.6→2.2배로37.5% 증가. 탱코는2강 이후 보스용 탄수·피해·간격이 동일. 뾰코는4강에서 이미5발 상한.','4/5강 보스 배율을1.6/1.6으로 제한하는 대조안. 뾰코5강 탄간 각도10°→7.5°는 별도 대조.','다른 값 고정 시5강 HP27.3% 감소. 뾰코 명중 집중이 좋아질 수 있으나 군중 공격 범위 감소. 보스 기본HP안과 함께 재검증 필요. 탱코 추가 공격력/연사 조정은 보류.'],
[3,'월드2가 숲profile0의 생성·이동 기준으로 돌아감. 첫 단계 약체HP1 비중이 높고 기계요새 나사봇·톱니벌은 모두HP1.','보스 문제 확인 후 약체HP1→2를 지역별로 하나씩 대조. 필요시 설원 발사간격 scale .95→.85–.90 검토.','한 방 처치 문턱이 바뀌므로 체감은 선형 증가가 아님. 생성 간격·상한은 우선 유지하여 단순 물량 증가를 피함.'],
[4,'320px 화면의25%안전대80px에서 반경12를 고려한 중심 통로는56px. 탱코 단축 종단속도는111.3px/s.','장벽75/25 유지. 실제 사람 검사 후 예고1.2→1.4–1.5초 또는 UI 가림 개선 중 선택.','탱코가 약22–33px 더 이동할 시간. 모든 위치에서 회피 보장은 아니며 다른 캐릭터가 너무 쉬워질 수 있음.'],
[5,'표본9회 중6회가 설원 입장부터5강. 최대 강화 이후 power 효과는0.','우선 지역별3기회/50:50 유지. 별도 선택안으로 월드1 기회3→2 대조.','모든 아이템 획득 가정의5강 확률96.16%→80.62%. 수집 보상 감소와 운 나쁜 플레이 악화 때문에 후순위.']]),'',
'보스HP를 올리면 그동안 생략되던 공격과 폭주가 드러난다. 따라서 HP안과 무기/체력 보정안을 독립적으로 검토한 뒤 조합해야 한다. 단순 정지DPS 산술 예측은 실제 이동·차단·회피·폭주를 반영하지 못한다.','',
'## 1. 현재 전체 구조와 지역별 차이','',
'기본은8지역×5단계=40단계다. 각 단계 일반 처치 목표는6이고,5단계도 일반6처치 뒤 보스가 등장한다. 개발자 직접5단계만 보스 즉시 시작이다.1–4단계 보너스500, 보스2,000, 일반100, 아이템몹200점을 유지한다.','',
'일반240처치/보스8/일반단계32회라면 아이템몹 제외 최소56,000점이다. **실제 일반 단계는 남은 적·예고가 모두 정리되어야 끝나므로6킬을 초과할 수 있다.** 자연 진행 표본의 일반 처치는259–272였고 추가 처치에도100점씩 지급됐다. 고정 한 마리씩 처치하는 회귀 검사의56,000점과 자연 진행 점수를 혼동하지 않는다. 명시OFF의20단계 및 기록 분리도 유지한다.','',
table(['지역','기본 보스HP','0/1/3/5강 HP','단계1→5 시도 간격','단계별 상한'],[[r['name'],20+r['combatProfile']*15,' / '.join(f'{(20+r["combatProfile"]*15)*d["bossMultipliers"][u]:g}' for u in [0,1,3,5]),f'{phase_rows[r["id"]*5]["attempt_interval"]:.2f}→{phase_rows[r["id"]*5+4]["attempt_interval"]:.2f}s',' / '.join(str(x['enemies_plus_warnings_cap']) for x in phase_rows[r['id']*5:r['id']*5+5])] for r in d['regions']]),'',
'간격은 생성 **시도** 주기다. 기존 legacyProbability=.22 때문에 일반 몬스터 입장 성공률은78%이며, 제한이 없을 때 평균 간격은 주기÷.78이다. 실제로는 상한, 전환,1.4초 예고, 처치 속도가 추가로 작용한다. 상한은 적+예고 합계다. 독립 아이템몹 도입 후에도 이 일반몹 입장 추첨이 남아 있으며 이번에는 수정하지 않았다.','',
'사막5단계 추적 기준102px/s, 탄속187px/s에서 설원의 추적 기준34.24/38.27/30.21/22.15px/s와 탄속85/76.5px/s로 내려간다. 설원 펭귄 돌진과 폭발은 별도 위협이지만, 적이 행동 전에 죽으면 패턴 난이도를 체감하기 어렵다.','',
'## 2. 몬스터와40단계 계량표','',
'월드1은 지역별 그림12/10/9/11종을 균등 선택하며 같은 지역 안에서는 전투 통계가 같다.38%의 ranged 모드가 별도로 붙는다. 추적 기준 속도는 단계당+5, 탄속은+8이다. 반복 발사간격은 기준×U(.85,1.40)/(1+.07×(단계−1)), 첫 발사는1+U(0,기준간격)이다. 회피·궤도·지그재그는 실제 속도 벡터를 바꾼다.','',
table(['월드1 지역','기본HP','단계1→5 추적','단계1→5 탄속','발사 기준s'],[[r['name'],1+r['combatProfile']//2,f'{d["tactics"][r["id"]]["move"]}→{d["tactics"][r["id"]]["move"]+20}',f'{d["tactics"][r["id"]]["bullet"]}→{d["tactics"][r["id"]]["bullet"]+32}',d['tactics'][r['id']]['interval']] for r in d['regions'][:4]]),'',
'일반 접촉·탄환·범위·레이저 피해는1이며 피격 무적은1.55초다. 전용 월드2 AI는 아래 통계로 덮어쓴다. 표에서 발사 수치가 없는 나사봇·톱니벌은 탄환을 쏘지 않는다. 드론의 공격은 투사체 속도가 없는 레이저다.','',
table(['지역/종류','HP','추적px/s','발사 기준/간격s','탄속px/s'],[[x['region_name']+' / '+x['id'],x['hp'],x['speed'],x.get('interval','예고·돌진/빔'),x.get('bullet','탄환 없음/빔')] for x in monster_rows if x['region']>=4]),'',
'설원 펭귄은0.8초 예고 후H×1.05를1.2초에 돌진하고0.8초 휴식하며 벽에서 멈춘다. 화산 도마뱀은0.32초 횡이동/0.88초 추적, 박쥐는.55/.8/.65/1초 지그재그, 갑충은.25초 예고/.7초 동안1타 방어/4.5초 회복이다. 폭풍 박쥐는.5초 예고/155px/s×.75초 돌진/1.2초 휴식이다.','',
'기계요새 나사봇은110px 안에서.45초 예고 후H×.4/100px/s 돌진,2.2초 휴식이다. 톱니벌은.60초 예고 후H×.7/145px/s,2.6초 휴식이다. 벽까지 실제 거리가 짧으면 단축된다. 드론은150–210px 거리를 유지하고.65초 예고/.28초 빔/3.1초 휴식, 빔 폭7·길이260이다. 포탑은.45초 예고/3.6초 주기/75px/s 포탄이다.','',
'다음 가중치 순서는 각 지역 config/spawns의4종 순서다. 월드1은 그림 균등이다. 시간은 정상 누적 자동 진행9회의 중앙값이며5단계에는 일반6킬 과정과 보스전이 포함된다.','',
table(['지역·단계','가중치%','평균HP','시도/평균입장s','상한','측정 단계s','최대 적/탄 중앙값'],[[r['name']+' '+str(r['phase']),weight_label(r),r['weighted_HP'],f'{r["attempt_interval"]:.2f}/{r["uncapped_expected_interval"]:.2f}',r['enemies_plus_warnings_cap'],r['median_seconds'],f'{r["median_peak_enemies"]}/{r["median_peak_bullets"]}'] for r in phase_rows]),'',
'상한과 실제 동시 개체 수는 다르다. 빠르게 처치하는 정책에서는 상한을 채우지 않는 경우가 많다. 개체별 전체 속성은 [monster-profiles.csv](monster-profiles.csv), 단계별 min/max는 [phase-metrics.csv](phase-metrics.csv)에 있다.','',
'## 3. 캐릭터 무기와 유효DPS','',
table(['캐릭터/강화','간격s','탄수/유도','개별피해','명목총DPS','탄속','관통'],[[heroes[w['hero']]+' '+str(w['upgrade']),f'{w["interval"]:.5f}',f'{w["projectiles"]}/{w["homing"]}',w['damage'],w['nominalDPS'],w['speed'],w['pierce']] for w in d['weapons']]),'',
'탱코 폭0~5강은17.5/45.5/51.1875/56.875/62.5625/68.25px, 높이29px다. 적 탄환과 충돌하면 양쪽이 소멸한다. 관통은 일반몹·보스에 같은 탄의 중복 피해를 허용하지 않는다. 현재 모든 탄의 explosion은0이므로 비활성 코드의 폭발 피해를 공격력에 합산하지 않았다.','',
'아래는160px의 정지한 반경48 표적에12초 발사한 유효DPS다. 원래 shoot, fireCooldown·탄 이동/유도 코드 조각, 충돌 함수를 사용했다. 초기 비행 시간과 프레임 양자화를 포함한다. 적 공격·타겟 이동·여러 몬스터 관통은 없는 별도 측정이다.','',
table(['캐릭터/강화','60Hz 유효DPS','120Hz 유효DPS'],[[heroes[h]+' '+str(u)]+[next(x['effectiveDPS'] for x in weapons if x['hero']==h and x['upgrade']==u and x['radius']==48 and x['distance']==160 and x['rate']==rate) for rate in [60,120]] for h in range(3) for u in [0,1,3,5]]),'',
'거리80/160/240, 표적 반경16/48,60/120Hz 전체144조건은 [weapon-assays.csv](weapon-assays.csv)에 있다. 뾰코1/3강은 가운데 탄이 없는 짝수 부채꼴이어서 작은 먼 표적에 명중하지 않을 수 있다.5강은3강보다 발수가 많아도160px 보스에서는 바깥 탄이 벗어난다. 빙글의 유도 안정성과 탱코의 HP·관통·차단은 단일 표적DPS만으로 평가할 수 없다.','',
'원래 발사 대기시간은 프레임을 넘긴 잔여시간을 누적하지 않아 주사율에 따른 차이가 있다. 향후 누적 방식 검토는 가능하지만 실제 공격 성능 변경이므로 이번에는 적용하지 않았다.','',
'## 4. 실제 보스 AI를 켠 통제 전투','',
'다음은 풀HP·아이템 없음·동일 자동 정책의 보스 처치 시간이다.0강은 개발자 초기 상태 비교용이고,1/3/5강은 등장 전에 강화값을 설정하여 실제 HP 보정을 받는다. 출현 직후 시작 위치와 완벽한 위치 정보·즉시 반응 정책이 고정되어 사람의 전투 시간과 다르다. 공격/피해는 실제 코드대로이며 무적·즉사는 사용하지 않았다.','']
for h in range(3):
 lines += ['### '+heroes[h], '', table(['지역','0강','1강','3강','5강'],[[r['name']]+[next(fmt(x['seconds']) if x['encounterDefeated'] else '사망/미처치' for x in bosses if x['hero']==h and x['encounter']['region']==r['id'] and x['encounter']['upgrade']==u and not x['encounter']['lowHP'] and x['encounter']['item']=='none') for u in [0,1,3,5]] for r in d['regions']]),'']
lines += ['월드1 보스는1/3/3/5발 부채꼴, 주기 max(.75,1.8−profile×.2−5×.055)초, 각 지역 기본 탄속+32다. 월드2의 전용 패턴과 가동·휴식은 다음과 같다. 상세 설정 전체는 baseline-metrics.json에 포함된다.','',
table(['보스','패턴과 시간'],[
['눈보라 거인왕','첫1.8초/휴식3초.3발80px/s·18°→6발65px/s·60°(시작각15° 증가)→폭발. 폭발 예고1.4/가동.25초, 반경 clamp(H×.18,56,74). 기본 순환 약10.65초. 탄상한9/수명3.4초.'],
['마그마 드래곤','첫1.8/휴식2.8초.3회 연사 간격.32초·88px/s·탄상한18. 분출 예고1.25/가동.25초·반경48–64. 브레스 예고1초→하향.2초→선택 방향3.8초 정확360°. 길이165–205. 회전 중 재추적 없음. 위치잡기 최대3초 등 추가.'],
['폭풍의 지배자','첫1.8/휴식1.9초(하한1.5). 탄막·회오리·쌍레이저, 같은 패턴 연속 제외. 경고.8/레이저 예고1·가동2초. HP50%에서2초 각성, 공격속도×1.2/탄속×1.1. 탄상한32·회오리최대3/5초.'],
['기가코어','첫1.4/휴식2.8초(폭주2.1). 레이저 예고.9/가동1.8초(폭주1.44),180°회전. 미사일 예고.7/2개·폭주3개/80·88px/s/수명3.4/유도1.6rad/s/최대12. 장벽 예고1.2/이동3초/75%·안전25%/4조합. HP50% 폭주 예고.8초.']]),'',
'플레이어는 transition 중에도 발사할 수 있지만 적 공격은 전환 중 억제된다.1.5초 보스 출현 안내 중 강한 무기로 보스를 죽이면 패턴의 실제 가동 기회가 사라진다. 패턴 자체가 약한 문제와 구분해야 한다. 폭주도 체력이 빨리 소진되면 체감되지 않는다.','',
'가동률은 해석을 구분해야 한다. 아래는 해당 패턴만 반복한다고 가정한 `피해 활성시간 ÷ (예고+활성+다음 휴식)`의 설정상 산술 비율이다. 실제 순서·위치잡기·각성·조기 처치·탄환 잔류가 있어 전체 전투의 점유율이나 실제 피격률은 아니다. 탄 발사 자체는 순간 이벤트이므로 탄환 수명과 상한을 함께 봐야 한다.','',
table(['패턴','계산 조건','설정상 활성 비율'],[
['설원 폭발','.25 / (1.4+.25+3)',f'{.25/(1.4+.25+3)*100:.1f}%'],
['화산 분출','.25 / (1.25+.25+2.8)',f'{.25/(1.25+.25+2.8)*100:.1f}%'],
['화산 브레스','4 / (1+4+2.8), 위치잡기 0–3초 추가',f'{4/(1+4+2.8+3)*100:.1f}–{4/(1+4+2.8)*100:.1f}%'],
['폭풍 레이저','2 / (1+2+1.9), 각성 후 세 시간 모두 ÷1.2',f'{2/(1+2+1.9)*100:.1f}%'],
['기가코어 레이저','일반1.8/(.9+1.8+2.8), 폭주1.44/(.9+1.44+2.1)',f'{1.8/(.9+1.8+2.8)*100:.1f}% / {1.44/(.9+1.44+2.1)*100:.1f}%'],
['기가코어 장벽','일반3/(1.2+3+2.8), 폭주3/(1.2+3+2.1)',f'{3/(1.2+3+2.8)*100:.1f}% / {3/(1.2+3+2.1)*100:.1f}%']]),'',
f"풀HP/HP1 × 아이템 없음/발밑 체력/발밑 강화 ×3캐릭터×1/3/5강×8지역 및0강 비교, 총480조건 중 {sum(x['encounterDefeated'] for x in bosses)}조건 처치, {sum(x['deaths'] for x in bosses)}조건 사망이었다. 이는 고정 정책·한 전투 시드의 실험 결과이며 사람 승률이 아니다. [boss-times.csv](boss-times.csv)에 실패 조건도 포함했다.",'',
'체력 자체는 공격력을 바꾸지 않는다. 발밑 power는 첫 틱에 원래+1 효과를 주며 보스HP는 등장 때 이미 결정되어 다시 증가하지 않는다. HP 아이템은+2/상한이고 최대 강화5에서 power 추가 효과는0이다. 게임에 보관형 인벤토리는 없으므로 여기서 보유 상태는 근처에 아직 줍지 않은 이월 아이템이 있다는 조건이다.','',
'## 5. 일반 단계의 강화·체력·아이템 조건','',
'각 지역 일반1단계에서1/3/5강 × 풀HP/HP1 × 없음/체력/강화 ×3캐릭터를 비교했다. 일반 스폰·AI·충돌·실제 피해·처치 목표는 그대로다. 새 아이템몹 기회만 진단 안에서0으로 두어 시작 강화와 지정 아이템 효과를 분리했다. 정상40단계 표본에는 원래 지역별3기회가 모두 적용된다.','',
f"총432조건 중 {sum(x['cleared'] for x in normals)}조건에서 단계를 완료했고 {sum(x['deaths'] for x in normals)}조건은 사망했다. 시간에는 시작 안내/예고와 남은 적 정리가 포함되며 실제 처치가6을 넘을 수 있다. 실패는 제외해 평균내지 않고 원본 [normal-phase-times.csv](normal-phase-times.csv)에 남겼다.",'',
'측정 중 사망한 조건은 아래와 같다. 실제 피해·게임 오버가 발생했다는 관찰이며 자동 검사 도구의 오류와는 구분한다. 나머지 조건의 성공을 사람의 생존 보장으로 일반화하지 않는다.','',
table(['전투','캐릭터','지역','시작 강화/HP','이월 아이템','사망까지s'],[['보스',heroes[x['hero']],d['regions'][x['encounter']['region']]['name'],f"{x['encounter']['upgrade']}/1",x['encounter']['item'],x['seconds']] for x in bosses if x['deaths']]+[['일반1단계',heroes[x['hero']],d['regions'][x['scenario']['region']]['name'],f"{x['scenario']['upgrade']}/1",x['scenario']['item'],x['seconds']] for x in normals if x['deaths']]),'']
for h in range(3):
 lines += ['### '+heroes[h]+' — 풀HP·아이템 없음, 목표6킬 단계 완료 초','',table(['지역','1강','3강','5강'],[[r['name']]+[next(fmt(x['seconds']) if x['cleared'] else '사망/미완료' for x in normals if x['hero']==h and x['scenario']['region']==r['id'] and x['scenario']['upgrade']==u and not x['scenario']['lowHP'] and x['scenario']['item']=='none') for u in [1,3,5]] for r in d['regions']]),'']
lines += ['## 6. 정상 월드1 누적 상태와 아이템','',table(['캐릭터','시드/정책','설원 강화/HP','전체초','일반/아이템몹 처치','실제점수','피해/차단'],[[p['hero'],str(p['seed'])+'/'+p['policy'],f'{p["snow_upgrade"]}/{p["snow_HP"]}',p['seconds'],f'{p["normal_kills"]}/{p["item_kills"]}',p['score'],f'{p["damage"]}/{p["blocked"]}'] for p in progress]),'',
f"9회 모두 실제40단계를 완료했다. 그러나 **사람의 클리어율100%라는 뜻이 아니다.** 설원 입장 강화는 {[p['snow_upgrade'] for p in progress]}이고, {sum(p['snow_upgrade']==5 for p in progress)}/9회가 이미5강이었다. ignore 정책도 우연한 명중/획득과 자동 보스 보상을 막지는 않았다. 수집 정책과 시드가 함께 달라지므로 모집단의 운 분포로 일반화하지 않는다.",'',
'다음은 같은 정상 진행 9회의 지역별 중앙값이다. 보스까지 시간에는 1–4단계와 5단계 일반 전투·전환이 포함되며, 처치 후 소멸 연출 시간은 제외한다. 출현·처치 시각은 원래 update 경계에서 1/60초 해상도로 관찰했다. 명시적 시각을 추가한 재실행9회에서도 이전 시간·물리·단계·경계·집계·보스 측정값이 모두 같았다. 각 경계의 체력·강화·이월 아이템은 route-samples.json의 boundaries, 72개 캐릭터·시드·지역 요약은 [regional-progression.csv](regional-progression.csv)에 있다. 이는 모든 위험 패턴을 끝까지 겪는 내구 시험은 아니다.','',
table(['지역','입장 강화 범위','지역 전체s','보스까지s','보스전s','최대 적탄 범위'],[[reg['name'],f"{min(x['entry_upgrade'] for x in regional if x['region']==reg['id'])}–{max(x['entry_upgrade'] for x in regional if x['region']==reg['id'])}",*[statistics.median(x[k] for x in regional if x['region']==reg['id']) for k in ['total_seconds','to_boss_seconds','boss_seconds']],f"{min(x['peak_enemy_bullets'] for x in regional if x['region']==reg['id'])}–{max(x['peak_enemy_bullets'] for x in regional if x['region']==reg['id'])}"] for reg in d['regions']]),'',
'사막→설원 경계에서는 같은 캐릭터·시드의 보스 시간을 직접 비교할 수 있다. 지역 전환 회복으로 체력이 보충되며 적의 추적·탄속·생성 기준도 숲 수준으로 내려간다. 따라서 개발자 강화0 보스전만으로 정상 누적 플레이의 난이도를 판단하면 이 격차를 놓친다.','',
'아이템몹은 지역별 서로 다른1–4단계3곳에서 일반1–4처치 후1.4초 예고를 거쳐 나온다. HP5/수명10초/80×64/r20이며125px 내에서 도주한다. 속도 기준은45+profile×8이다. 처치하면50:50 체력+2/강화+1, 아이템은16초간 떠다니고 단계/지역을 넘어 남은 수명을 보존한다. 아이템몹 처치는 일반 목표에 포함되지 않는다. 보스 보상도 독립50:50 즉시 지급이다. **보스 보상 후 지역 이동 체력+2**가 최대HP 안에서 적용된다. 최종 보스 뒤에는 다음 지역 회복이 없다.','',
'다음은 확정 수집률을 가정한 정확한 이항 모형으로 실측 확률이 아니다. 월드1 보스4회와 지역별 아이템몹 기회12회(대조안8회), power 확률.5를 사용한다. 도주·사망·유효 수명·추적 선택을 직접 반영하지 않아 상한/민감도 참고용이다.','',table(['지역당 기회','가정 수집률','평균 강화(상한5)','5강 확률'],[[m['quota'],m['assumed_collection_rate'],m['mean_upgrade'],f'{m["probability_level5"]*100:.2f}%'] for m in models]),'',
'## 7. 기가코어 안전대와 실제 이동','',table(['높이','안전대/중심통로','캐릭터','명목 상한','단축 종단속도','1.2초 이동(산술근사)'],[[c['height'],f'{c["safe_band"]}/{c["usable_center_band"]}',c['hero'],c['nominal_speed_cap'],c['unit_axis_terminal_speed'],c['distance_from_rest_in_warning']] for c in corridors]),'',
'거리 표는 연속시간 가속·마찰식의 산술 근사이며 실제 프레임별 위치 적분과는 약간 다를 수 있다. 한 축 단위 입력에서 속도는 accel/drag로 수렴한다. 탱코는473/4.25=111.29px/s이며 명목 상한204보다 낮다. 대각 두 축이 각각1인 입력은 별도지만 표는 한 축이다. 벽까지 실제 시간은 예고1.2초+현재x까지 이동 시간이다. 진입측에 가깝고 반대 끝 안전대로 가야 하는 상황은 즉시 반응하더라도 불리하다. 항상 회피 가능하다는 보장은 아니다.','',
'25% 안전대에서 반경12를 고려한 플레이어 중심 통로는 H×.25−24다. 반대 끝에서 위쪽 안전대 중심 한계까지는 약H×.75를 이동해야 한다. UI는 이동을 막는 벽이 아니지만 플레이어를 가릴 수 있다. [safe-band-occlusion.json](safe-band-occlusion.json)은 UI/보스HP 박스를12px 확장한 **보수적 중심 위치 가림**이다. 실제 픽셀 가림 확률이나 피해 확률과 다르다.','']
if (OUT/'safe-band-occlusion.json').exists():lines += [table(['화면','안전대','중심 통로높이','보수적 UI 가림'],[[str(x['viewport']),x['band'],x['player_center_band_height'],f'{x["conservative_occlusion_ratio"]*100:.1f}%'] for x in load('safe-band-occlusion.json')]),'']
lines += ['## 8. 실제 코드 변경·기록 보존·검증','',
'제품 변경은 표시 자산3개뿐이다.4지역/4보스 이름,40단계 클리어·도움말·순위표 문구를 정리하고 일반20/40 플레이의 개발 안내를 숨겼다. 개발자 바로 시작은 유지하며 설원의 숲 임시BGM 사실도 남겼다. 시험 표기를 제거한 것이 새 콘텐츠의 정식 승인이나 새 음원 제작을 뜻하지는 않는다.','',
'ID/key/route/prototype/profile/trialMode와 기록4키는 그대로다. 예전 regionName의(시험)은 저장 원문을 유지하고 현재 registry 이름으로 표시한다. 새 결과 저장 후에도 기존 알려진 필드 전체가 그대로인지 검사했다.19개 정확한 표시 차분을 되돌리면 기준과 같고, index 전체(멀티터치 나가기 포함)와 나머지128자산은 바이트가 같다.','',
'일반/오프라인 UI는4지역×1·5단계×3화면과 도움말·결과·순위표를 검사한다. 과거 기록4키, 새 기록 후 과거 필드, 개발자 보스 즉시 시작,3점 터치 후 click 누락·취소·재열기를 포함한다. 최종 회귀 통과/실패/미실행은 [validation.md](validation.md)와 [test-summary.json](test-summary.json)에 분리한다.','',
'## 9. 재현 방법과 한계','',
'진단은 새 Chromium 프로필에서만 수행한다. 봇은 적·위험 좌표를 완벽히 알고 지연 없이 가상 센서 명령과 원래 조이스틱 키보드 핸들러를 사용한다. 원래 가속·마찰·회전·발사·피해·보상 코드는 유효하다. 강제 무적, 즉사, 자동 부활은 없다. 렌더RAF만 멈추고 원래 update를60Hz로 진행하므로 시간은 시뮬레이션 초이며 실제 기기FPS/사람 조작 시간과 다르다.','',
'진단의 효과음 출력만 비활성화했으며 음악 재생 검사는 별도로 수행했다. 첫 발사 대기시간은 비교를 위해 새 세션의0으로 통일했다. 원래 start가 이전 게임의 잔여 fireCooldown을 초기화하지 않는 제품 동작은 수정하지 않았다. 정지 표적 발사 루프도 원래 코드 조각 그대로이며60/120Hz를 나눴다. 동일 시드/정책 재실행에서 시간·단계·보스·발사·피해가 같았다.','',
'이전 사용 한도 중단 후 임시 디렉터리가 초기화되어 미커밋 복사본과 당시 원본 검사 로그가 사라졌다. 대화에 남은 명세·코드·측정 방법으로 복구했고, 이 보고서의 데이터와 최종 검사 결과는 복구 후 재실행에서 확보했다. 이전 관찰을 새 원본 데이터인 것처럼 합산하지 않았다. 복구 과정과 이전 진단 오류 요약은 recovery.md에 기록한다. 영구 체크포인트에도 작업을 보관한다.','',
'실제 Galaxy 삼성 인터넷/Chrome, 물리 센서, 스피커 청취, 다운로드 파일 연결, 사람의 명중·반응·체감 난이도는 미검증이다. 정상9회와 통제 조건912회의 결과를 사람의 승률/위험 확률로 해석하지 않는다. 권장 수치에는 별도 검토가 필요하다.','',
'```bash','PYTHONDONTWRITEBYTECODE=1 python scripts/analyze_world_balance.py','PYTHONDONTWRITEBYTECODE=1 python scripts/measure_world_route_timing.py','PYTHONDONTWRITEBYTECODE=1 python scripts/analyze_normal_phase_balance.py','PYTHONDONTWRITEBYTECODE=1 python scripts/measure_safe_corridors.py','PYTHONDONTWRITEBYTECODE=1 python scripts/summarize_world_balance.py','PYTHONDONTWRITEBYTECODE=1 python tests/world_balance_labels_preservation.py','```','',
'원본은 definitions.json, route-samples.json, weapon-assays.json, boss-encounters.json, normal-encounters.json이다. baseline-metrics.json은40단계 표·설정·소스SHA256·가정 모형을 포함한다. main 병합과 Pages 배포는 진행하지 않는다.']
lines += ['', '## 10. 화면 비교와 갤럭시 결과물', '',
'수정 전은 기준 커밋의 표시 모듈 3개를 읽기 전용으로 제공하고, 수정 후는 현재 코드를 사용한 실제 Chromium 화면이다. 비교 장면은 같은 상태로 통제했으므로 전투 시간·생존 측정 증거와는 별개다. 각 링크는 원본 해상도 PNG이며, 아래 표 이외에도 before 폴더와 일반·오프라인 검사 폴더에 3개 화면 크기 전체를 보관한다.', '']
gallery=[]
for region in range(4,8):
 for phase in [1,5]:
  name=f'region-{region}-phase-{phase}-915x412.png';compact=f'region-{region}-phase-{phase}-568x320.png'
  gallery.append([d['regions'][region]['name']+f' {phase}/5',f'[이전](screenshots/before/{name})',f'[수정 후](tests/world_balance_labels-native/{name})',f'[568×320](tests/world_balance_labels-native/{compact})'])
for stem,label in [('help','게임 방법'),('leaderboard','40단계 순위표'),('full40-clear','최종 클리어')]:
 name=f'{stem}-915x412.png';compact=f'{stem}-568x320.png'
 gallery.append([label,f'[이전](screenshots/before/{name})',f'[수정 후](tests/world_balance_labels-native/{name})',f'[568×320](tests/world_balance_labels-native/{compact})'])
lines += [table(['화면','수정 전915×412','수정 후915×412','수정 후 소형 화면'],gallery),'',
'[최신 갤럭시 ZIP](https://github.com/26aiera11-cpu/helicopter-game/raw/refs/heads/feature/world-balance-audit-clean-labels/dist/heli_trio_galaxy_test.zip) · [패키지 크기·SHA256·CRC](package.json) · [압축해제·코드 원문 확인](standalone-integrity.json). ZIP에는 HTML 하나만 들어 있다. 다운로드 후 압축을 풀고 HTML을 브라우저에서 연다. 실제 삼성 인터넷의 로컬 파일 연결과 스피커 청취는 사용자 기기에서 확인해야 한다.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');print('Summary:',len(phase_rows),'phases;',len(monster_rows),'monster rows;',len(runs),'routes;',len(bosses),'boss +',len(normals),'normal cases')
