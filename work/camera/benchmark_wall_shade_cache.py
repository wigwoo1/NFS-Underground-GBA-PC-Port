from pathlib import Path
import subprocess,sys,os,json
p=Path(__file__).resolve().parent;runs=[]
for enabled in (False,True,False,True):
 env=dict(os.environ);env['BENCH_NF_TEST_WALL_SHADE_LOOKUP_CACHE']='1' if enabled else '0'
 r=subprocess.run([sys.executable,str(p/'benchmark_race_capture.py'),'direct-dirty-profile'],env=env,capture_output=True,text=True,timeout=60)
 assert r.returncode==0,r.stdout+r.stderr
 report=json.loads(r.stdout.split('BENCHMARK_JSON=')[-1]);report['cache_enabled']=enabled;runs.append(report)
 assert report['completions']==75 and report['original_ram_exact'] and report['save_unchanged']
 if enabled:assert report['wall_shade_lookup_stats'][0]>0
 else:assert report['wall_shade_lookup_stats'][0]==0
assert len({tuple(x['ram_sha256']) for x in runs})==1
out=dict(result='PASS_MATCHED_COMPONENT_STATE',runs=runs,scope='Alternating fresh-process300update profiles; instrumentation/scheduling affect timings. No live60fps proof.')
(p/'wall-shade-cache-benchmark.json').write_text(json.dumps(out,indent=2))
print(json.dumps([dict(enabled=x['cache_enabled'],wall_ms=x['wall_ms'],cpu_ms=x['cpu_ms'],hits=x['wall_shade_lookup_stats'][0]) for x in runs],indent=2))
