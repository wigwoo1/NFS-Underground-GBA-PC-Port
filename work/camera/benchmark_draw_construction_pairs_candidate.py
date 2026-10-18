import subprocess,sys,json,statistics
from pathlib import Path
rows=[]
for trial in range(4):
 for mode in (['original','cache'] if trial%2==0 else ['cache','original']):
  result=subprocess.run([sys.executable,'work/camera/benchmark_draw_construction_process_candidate.py',mode],check=True,capture_output=True,text=True)
  row=json.loads(result.stdout);row['trial']=trial;rows.append(row)
assert len({x['frame_sha256'] for x in rows})==1
summary={mode:{release:statistics.median([x['results'][release]['median_ms'] for x in rows if x['mode']==mode]) for release in ['False','True']} for mode in ['original','cache']}
out=dict(result='PASS_SEPARATE_PROCESS_CAPTURE_DERIVED_CONSTRUCTION_COST',summary_median_ms=summary,rows=rows,scope='Four alternating pairs of isolated child processes; five capture-derived array inputs, captured contiguous frame binding. Two lifetime models (previous retained during construction versus explicitly released). 50warmups1000samples each. No renderer/sky attachment/live GC or cadence proof; host uncontrolled.')
Path('work/camera/prototype-runs/draw-construction-process-cost-20261009.json').write_text(json.dumps(out,indent=2));print(summary)
