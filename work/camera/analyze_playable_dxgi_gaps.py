"""Join successful DXGI callbacks by ordered invocation and strict timestamp containment."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());trace=json.loads(Path(sys.argv[2]).read_text());g=json.loads(Path(sys.argv[3]).read_text())
a=[s for s in r['presentation_samples'] if s.get('presentation_backend')=='dxgi_flip_sequential'];p=trace['rows'];assert len(a)==len(p)>0
mapping={};names=trace['phases']
for s,t in zip(a,p):
 assert len(t)==18 and t[16]==0 and s['dxgi_present_result']==0
 assert all(x<=y for x,y in zip(t[:7],t[1:8]))
 assert s['native_commit_stage_ns'][3]<=t[0]<=t[7]<=s['native_commit_stage_ns'][4]
 mapping[s['display_index']]=t
rows=[]
for gap in g['largest']:
 t=mapping[gap['display_index']];parts={n:(t[i+1]-t[i])/1e6 for i,n in enumerate(names)}
 rows.append(dict(display_index=gap['display_index'],gap_ms=gap['gap_ms'],consumer_parts=gap['parts'],dxgi_parts_ms=parts,dominant_dxgi=max(parts,key=parts.get)))
o=dict(result='PASS_ORDERED_CALLBACK_CONTAINMENT',callbacks=len(a),rows=rows,scope='Ordinal join validated by exact callback containment for every row; native phases include waits/scheduling, no exclusive cause or physical scanout proof.')
Path(sys.argv[4]).write_text(json.dumps(o,indent=2));print(json.dumps(o,indent=2))
