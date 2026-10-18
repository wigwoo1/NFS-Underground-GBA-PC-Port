"""Attribute diagnostic native input wall time; includes scheduling, not exclusive CPU."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text())
rows=[x for x in r['presentation_samples'] if x.get('native_input_stage_ns') is not None]
assert rows
names=['message_pump','focus_keyboard','controller_access','snapshot_lock']
def stats(a):
 return dict(count=len(a),total_ms=sum(a)/1e6,median_ms=statistics.median(a)/1e6,max_ms=max(a)/1e6)
for x in rows:
 assert len(x['native_input_stage_ns'])==4 and all(n>=0 for n in x['native_input_stage_ns'])
 assert sum(x['native_input_stage_ns'])<=x['native_input_poll_ns']+1000
out=dict(scope='Native wall stage duration, includes OS calls and scheduling; no exclusive CPU or physical controller verification',stages={name:stats([x['native_input_stage_ns'][i] for x in rows]) for i,name in enumerate(names)},largest=[]) 
for x in sorted(rows,key=lambda x:x['native_input_poll_ns'],reverse=True)[:10]:
 out['largest'].append(dict(refresh=x['refresh'],total_ms=x['native_input_poll_ns']/1e6,stages_ms=dict(zip(names,[n/1e6 for n in x['native_input_stage_ns']]))))
p.with_suffix('.input-stages.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

