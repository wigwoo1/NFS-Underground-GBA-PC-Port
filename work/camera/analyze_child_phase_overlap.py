"""Exact child phase intervals joined to concurrent original updates."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
keys=['started_ns','decoded_ns','initialized_ns','constructed_ns','sampled_ns','encoded_ns','sent_ns'];names=['decode','history_init','construct','precompute','encode','output_send_ack']
for s in r['world_preparation_stage_samples']:
 b=s['child_stages']['child_boundaries'];points=[b[k] for k in keys];assert points==sorted(points)
 for name,start,end in zip(names,points,points[1:]):
  overlap=sum(max(0,min(end,u['completed_ns'])-max(start,u['started_ns'])) for u in r['original_update_samples'])
  assert overlap<=end-start
  rows.append(dict(older=s['older'],newer=s['newer'],phase=name,wall_ms=(end-start)/1e6,original_update_overlap_ms=overlap/1e6,started_ns=start,completed_ns=end))
out=dict(checked_jobs=len(r['world_preparation_stage_samples']),phases=len(rows),totals={name:dict(wall_ms=sum(x['wall_ms'] for x in rows if x['phase']==name),original_update_overlap_ms=sum(x['original_update_overlap_ms'] for x in rows if x['phase']==name)) for name in names},largest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:15],scope='Concurrent host elapsed spans, not additive CPU attribution or proof of scheduling cause. Output phase includes serialization, publication and acknowledgement.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
