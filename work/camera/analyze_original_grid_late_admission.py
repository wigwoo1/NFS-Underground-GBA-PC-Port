"""Bounded late-admission audit: preserve source clock and distinguish completion from wait-entry."""
import json,sys
from pathlib import Path
reports=[]
for filename in sys.argv[1:-1]:
 r=json.loads(Path(filename).read_text()); rows=r['presentation_samples']; selected=[]
 for row in rows:
  if row['native_result']!=1:continue
  tx=row['native_transaction'];w=tx['wait'];c=tx['commit']
  assert len(w)==4 and len(c)==8 and w[2]>=w[0]
  selected.append(dict(key=tuple(c[:2]),index=c[4],entry=w[0],deadline=w[1],late=w[0]-w[1]))
 assert len(selected)>=2
 adjacent=[]
 for a,b in zip(selected,selected[1:]):
  if a['key']==b['key'] and b['index']==a['index']+1:
   deadline_step=b['deadline']-a['deadline'];assert deadline_step in (16666666,16666667)
   drift=(b['entry']-a['entry'])-deadline_step
   assert drift==b['late']-a['late']
   adjacent.append(drift)
 assert len(adjacent)==len(selected)-1
 reports.append(dict(raw=str(Path(filename).resolve()),retained_samples=len(selected),adjacent=len(adjacent),first_late_ms=selected[0]['late']/1e6,last_late_ms=selected[-1]['late']/1e6,net_lateness_growth_ms=sum(adjacent)/1e6,deadline_grid_unchanged=True,source_index_contiguous=True))
out=dict(result='PASS_BOUNDED_ORIGINAL_GRID_LATE_ADMISSION_AUDIT',runs=reports,scope='Last retained presentation window only, not full-run clock/throughput/latency qualification. Native wait entry delta minus fixed deadline delta exactly accounts for accumulated lateness; source game speed is not inferred.')
Path(sys.argv[-1]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
