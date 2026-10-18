from pathlib import Path
import subprocess,sys,os,json
p=Path(__file__).resolve().parent;env=dict(os.environ);env.update(BENCH_UPDATES='720',BENCH_LIVE_ROUTE='1');runs=[]
for mode in ('baseline','direct-dirty-profile','direct-dirty-profile'):
 r=subprocess.run([sys.executable,str(p/'benchmark_race_capture.py'),mode],env=env,capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+r.stderr
 report=json.loads(r.stdout.split('BENCHMARK_JSON=')[-1]);runs.append(report)
 if mode=='baseline':env['BENCH_BASELINE_JSON']=json.dumps(report)
assert all(x['ram_sha256']==runs[0]['ram_sha256'] for x in runs)
assert runs[1]['completion_ledger']==runs[2]['completion_ledger'] and runs[1]['completion_ledger']
assert len(set(tuple(x) for x in runs[1]['completion_ledger']))==len(runs[1]['completion_ledger'])
out=dict(result='PASS_720_ROUTE_COMPONENT_STATE',runs=runs,scope='Same720original inputs as live steering phases without GPU/presentation; no fullscene60fps proof.')
(p/'capture-720-route-benchmark.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
