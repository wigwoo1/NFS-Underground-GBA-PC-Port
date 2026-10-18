"""Attribute producer wall boundaries and label observed capture subintervals."""
import json,statistics,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for x in r['original_update_samples']:
 b=x['native_boundary'];assert x['started_ns']<=b[0]<=b[1]<=x['completed_ns']
 p=x.get('capture_profile');assert p is not None and len(p)==6
 rows.append(dict(refresh=x['refresh'],wrapper_wall_ms=(x['completed_ns']-x['started_ns'])/1e6,native_wall_ms=(b[1]-b[0])/1e6,wrapper_before_ms=(b[0]-x['started_ns'])/1e6,wrapper_after_ms=(x['completed_ns']-b[1])/1e6,native_cycles=b[2],quantized_cpu_ms=b[4]/1e6,capture=dict(event_wall_ms=p[0]/1e6,event_calls=p[1],layer_capture_wall_ms=p[2]/1e6,layer_rows=p[3],original_scanline_wall_ms=p[4]/1e6,original_scanline_rows=p[5])))
reference=statistics.median(x['native_cycles']/x['native_wall_ms'] for x in rows if 0<x['native_wall_ms']<10)
for x in rows:x['cycle_density_relative_to_short_updates']=(x['native_cycles']/x['native_wall_ms'])/reference
out=dict(result='PASS_NATIVE_BOUNDARY_CONTAINMENT',updates=len(rows),median_native_ms=statistics.median(x['native_wall_ms'] for x in rows),longest=sorted(rows,key=lambda x:x['native_wall_ms'],reverse=True)[:24],scope='Capture event/layer/original-scanline wall intervals include waits/descheduling. Quantized CPU may report zero despite executed cycles. Remaining native time is unattributed, not automatically scheduling time. No original-speed or capture-policy change.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(updates=len(rows),longest=out['longest'][:2]),indent=2))
