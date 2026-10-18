"""Repeated fixed-input native capture comparison; no live timing certificate."""
import subprocess,sys,json,statistics
from pathlib import Path
runs=[]
for mode in ('bus','direct','direct','bus'):
 r=subprocess.run([sys.executable,'work/camera/benchmark_race_capture.py',mode],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr+r.stdout
 runs.append(json.loads(r.stdout.split('BENCHMARK_JSON=')[-1]))
assert len({tuple(x['ram_sha256']) for x in runs})==1
summary={m:{k:statistics.median(x[k] for x in runs if x['mode']==m) for k in ('wall_ms','cpu_ms','median_ms')} for m in ('bus','direct')}
result=dict(runs=runs,summary=summary,exact_original_ram=True,scope='fixed300originalinputs,noGPU/preparation/presentation,2passespermode')
Path('work/camera/prototype-runs/repeated-capture-modes.json').write_text(json.dumps(result,indent=2));print(summary)
