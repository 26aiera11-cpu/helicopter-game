"""Reproduce all/current selected suites without hiding incomplete results."""
import argparse,concurrent.futures,json,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--workers',type=int,default=2);parser.add_argument('--only',nargs='+')
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
known=[r['suite'] for r in json.loads((ROOT/'docs/review/volcano-monster-player-visual-fix/test-summary.json').read_text())['suites']]
known+=['volcano_combat-native','volcano_combat-offline','volcano_boss-native','volcano_boss-offline','volcano_boss_masks','volcano_breath_art-native','volcano_breath_art-offline','volcano_mixed-native','volcano_mixed-offline','volcano_bgm-native','volcano_bgm-offline','storm_sky-native','storm_sky-offline','storm_sky_edges','storm_background_fit-native','storm_background_fit-offline','storm_background_integrity','storm_sky_bgm-native','storm_sky_bgm-offline','machine_fortress-native','machine_fortress-offline']
names=args.only or known
assert set(names)<=set(known) and 1<=args.workers<=3
def run(name):
    stem=name.removesuffix('-native').removesuffix('-offline');folder=args.artifacts/name;folder.mkdir(parents=True,exist_ok=True)
    command=['python',str(ROOT/'tests'/f'{stem}.py'),'--artifacts',str(folder.resolve())]+(['--standalone'] if name.endswith('-offline') else [])
    begin=time.monotonic()
    with (folder/'run.log').open('w') as log:
        try:code=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
        except subprocess.TimeoutExpired:code=124
    p=folder/'test-results.json';data=json.loads(p.read_text()) if p.exists() else {}
    observed=len(data.get('passed',[])) or sum(s.startswith('PASS:') for s in (folder/'run.log').read_text().splitlines())
    result={'suite':name,'exit_code':code,'groups':observed if code==0 else 0,'observed_groups_before_failure':observed if code else 0,'seconds':round(time.monotonic()-begin,2),'command':command}
    print(json.dumps(result,ensure_ascii=False),flush=True);return result
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
    for future in concurrent.futures.as_completed([pool.submit(run,name) for name in names]):
        results.append(future.result());(args.artifacts/'suite-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
raise SystemExit(1 if any(r['exit_code'] for r in results) else 0)
