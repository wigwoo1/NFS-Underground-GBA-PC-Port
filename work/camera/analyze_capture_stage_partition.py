"""Partition measured producer capture without conflating cycle count with CPU time."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for x in r['producer_cycle_samples']:
 reads=x['frame_read_boundaries'];assert len(reads)==2 and reads[0]['query'] and not reads[1]['query']
 for q in reads:assert q['success'] and q['started_ns']<=q['native'][0]<=q['native'][1]<=q['completed_ns']
 native=sum(q['native'][1]-q['native'][0] for q in reads)/1e6
 outer=sum(q['completed_ns']-q['started_ns'] for q in reads)/1e6
 copy=(x['owned_bytes_copy']['completed_ns']-x['owned_bytes_copy']['started_ns'])/1e6
 rows.append(dict(refresh=x['refresh'],capture_ms=x['ns']/1e6,frame_read_ms=x['stages']['frame_read_ns']/1e6,native_read_ms=native,wrapper_outside_native_ms=outer-native,immutable_copy_ms=copy,native_read_cycles=sum(q['native'][2] for q in reads),frame_stage_cycles=x['stage_thread_cycles']['frame_read_ns'],graph_ms=x['stages']['graph_decode_match_ns']/1e6,graph_cycles=x['stage_thread_cycles']['graph_decode_match_ns'],submit_ms=x['stages']['worker_submit_ns']/1e6))
keys=('capture_ms','frame_read_ms','native_read_ms','wrapper_outside_native_ms','immutable_copy_ms','graph_ms','submit_ms')
summary={k:dict(median=statistics.median(x[k] for x in rows),max=max(x[k] for x in rows)) for k in keys}
out=dict(result='PASS_CAPTURE_BOUNDARY_PARTITION',captures=len(rows),summary=summary,slowest=sorted(rows,key=lambda x:x['capture_ms'],reverse=True)[:10],rows=rows,scope='Ordered actual native start/end timestamps. Native duration may include scheduling or lock waits; QueryThreadCycleTime is cycles, not calibrated CPU milliseconds. Instrumented run, not physical scanout or causal speed proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(summary);print(out['slowest'][0])
