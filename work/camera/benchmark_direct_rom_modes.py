"""ABBA fixed-input comparison of optional canonical ROM copies."""
import subprocess,sys,os,json,statistics
from pathlib import Path
runs=[]
for enabled in (False,True,True,False):
 env=dict(os.environ);env['BENCH_NF_TEST_DIRECT_CAPTURE_ROM']='1' if enabled else '0'
 r=subprocess.run([sys.executable,'work/camera/benchmark_race_capture.py','direct'],env=env,capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr+r.stdout
 result=json.loads(r.stdout.split('BENCHMARK_JSON=')[-1]);result['direct_rom']=enabled;runs.append(result)
assert len({tuple(x['ram_sha256']) for x in runs})==1
assert all(x['completion_ledger']==runs[0]['completion_ledger'] for x in runs)
summary={str(enabled):{k:statistics.median(x[k] for x in runs if x['direct_rom']==enabled) for k in ('wall_ms','cpu_ms','median_ms')} for enabled in (False,True)}
out=dict(result='PASS',runs=runs,summary=summary,exact_original_ram=True,exact_completion_ledger=True,scope='ABBA fixed300originalinputs component; excludes live GPU/preparation/scheduling, no60fpsproof')
Path('work/camera/prototype-runs/repeated-direct-rom-modes.json').write_text(json.dumps(out,indent=2));print(summary)
