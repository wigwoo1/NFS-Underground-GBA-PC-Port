"""Separate measured bridge hooks from original refresh duration, without changing logic."""
import csv,json,statistics,sys
from pathlib import Path
p=Path('work/camera');path=Path(sys.argv[1]);rows=list(csv.DictReader(path.open()));assert rows
stages=['live_capture','layer_capture','original_scanline']
samples=[]
for i,row in enumerate(rows):
 assert int(row['index'])==i and int(row['after'])==int(row['before'])+1
 total=int(row['end_ns'])-int(row['start_ns']);assert total>=0
 times={key:int(row[key+'_ns']) for key in stages}
 assert sum(times.values())<=total, 'Hook measurements overlap or exceed original refresh'
 times['other_simulation_and_hook_overhead']=total-sum(times.values())
 times['total']=total
 samples.append(dict(index=i,refresh=int(row['after']),ms={k:v/1e6 for k,v in times.items()}))
assert any(int(r['original_scanline_calls']) for r in rows), 'Capture profiling was not enabled'
summary={}
for key in samples[0]['ms']:
 values=sorted(s['ms'][key] for s in samples)
 summary[key]=dict(median=statistics.median(values),p95=values[int(.95*len(values))],maximum=max(values),total_ms=sum(values))
report=dict(result='PASS',refreshes=len(rows),stage_ms=summary,slowest=sorted(samples,key=lambda s:s['ms']['total'],reverse=True)[:12],scope='Diagnostic original-refresh hook timing; timestamps add overhead and include OS preemption. Other simulation is a residual, not native game-logic profiling. Does not verify 60fps or authorize removing original renderer work.')
(p/'original-refresh-profile-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
