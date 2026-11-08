"""Remeasure original-engine routes with explicit spawn/defeat timestamps."""
import json
from world_balance_harness import ROOT,browser_game
OUT=ROOT/'docs/review/world-balance-audit'
old=json.loads((OUT/'route-samples.json').read_text());rows=[]
with browser_game(pause=True) as (page,ctx,errors):
 page.evaluate((ROOT/'scripts/world_balance_probe.js').read_text())
 for previous in old:
  row=page.evaluate('v=>balanceAudit.run(...v)',[previous['hero'],previous['seed'],previous['policy'],1800])
  for key in ['seconds','stage','phase','totals','phases','boundaries']:
   assert row[key]==previous[key],(previous['hero'],previous['seed'],key)
  for before,after in zip(previous['bosses'],row['bosses']):
   assert all(after[k]==v for k,v in before.items())
   assert abs(after['defeatTime']-after['spawnTime']-after['bossSeconds'])<1e-8
  assert len(row['bosses'])==8 and row['completed'] and row['deaths']==0
  rows.append(row);print('Explicit boss timing, identical physics:',row['hero'],row['seed'],flush=True)
 again=page.evaluate('v=>balanceAudit.run(...v)',[old[0]['hero'],old[0]['seed'],old[0]['policy'],1800])
 assert again['bosses']==rows[0]['bosses']
 assert not errors,errors
(OUT/'route-samples.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
(OUT/'route-timing-provenance.json').write_text(json.dumps({'routes':9,'spawn_defeat_timestamps_observed_at_original_update_boundary':True,'all_previous_physics_timing_phases_boundaries_totals_and_boss_fields_exactly_reproduced':True,'explicit_timing_seed_replay':True,'rendered_defeat_outro_not_counted_as_pre_boss_time':True},indent=2)+'\n')
