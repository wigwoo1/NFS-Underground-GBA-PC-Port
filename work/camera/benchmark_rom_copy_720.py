from pathlib import Path
import subprocess,sys,os,json
p=Path(__file__).resolve().parent;env=dict(os.environ);env.update(BENCH_UPDATES='720',BENCH_LIVE_ROUTE='1');env.pop('BENCH_NF_TEST_VERIFY_CAPTURE_ROM',None);env.pop('BENCH_NF_TEST_WALL_SHADE_LOOKUP_CACHE',None)
reference=json.loads((p/'capture-720-route-benchmark.json').read_text());baseline=reference['runs'][0];ledger=reference['runs'][1]['completion_ledger'];env['BENCH_BASELINE_JSON']=json.dumps(baseline);runs=[]
for enabled in (False,True,False,True):
 env['BENCH_NF_TEST_DIRECT_CAPTURE_ROM']='1' if enabled else '0'
 r=subprocess.run([sys.executable,str(p/'benchmark_race_capture.py'),'direct-dirty-profile'],env=env,capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+r.stderr
 row=json.loads(r.stdout.split('BENCHMARK_JSON=')[-1]);row['rom_copy_enabled']=enabled
 assert row['completion_ledger']==ledger and row['ram_sha256']==baseline['ram_sha256']
 assert (row['rom_copy_stats'][0]>0)==enabled and row['rom_copy_stats'][2]==0
 runs.append(row)
 print(json.dumps(dict(enabled=enabled,wall_ms=row['wall_ms'],cpu_ms=row['cpu_ms'],scenes=row['completions'])),flush=True)
out=dict(result='PASS_FULL_ROUTE_ROM_COPY_PARITY',runs=runs,scope='Alternating fresh720input component processes with exact185scene ledger and baseline RAM; profiled, no live60fps proof.')
(p/'rom-copy-720-benchmark.json').write_text(json.dumps(out,indent=2))
