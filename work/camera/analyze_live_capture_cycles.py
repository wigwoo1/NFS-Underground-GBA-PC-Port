"""Summarize measured capture execution cycles, without converting them to CPU time."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for x in r['original_update_samples']:
 c=x['capture_execution_cycles'];assert len(c)==3 and c[0]>=c[1]+c[2]>0
 b=x['native_boundary'];p=x['capture_profile']
 rows.append(dict(refresh=x['refresh'],native_wall_ms=(b[1]-b[0])/1e6,whole_update_cycles=c[0],layer_cycles=c[1],scanline_cycles=c[2],layer_cycle_fraction=c[1]/c[0],scanline_cycle_fraction=c[2]/c[0],layer_wall_ms=p[2]/1e6,scanline_wall_ms=p[4]/1e6))
total=sum(x['whole_update_cycles'] for x in rows)
out=dict(result='PASS_CAPTURE_CYCLE_COVERAGE',updates=len(rows),layer_fraction_of_total_cycles=sum(x['layer_cycles'] for x in rows)/total,scanline_fraction_of_total_cycles=sum(x['scanline_cycles'] for x in rows)/total,median_layer_fraction=statistics.median(x['layer_cycle_fraction'] for x in rows),longest=sorted(rows,key=lambda x:x['native_wall_ms'],reverse=True)[:16],scope='Executed cycles include added counter overhead; wall intervals include scheduling/driver waits. Independent counter experiment, not exclusive slowdown causality or smooth60fps proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(updates=out['updates'],layer_fraction=out['layer_fraction_of_total_cycles'],scanline_fraction=out['scanline_fraction_of_total_cycles'],longest=out['longest'][:2]),indent=2))
