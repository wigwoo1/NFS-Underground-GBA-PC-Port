"""Validate scoped completion barriers and distinguish them from SwapBuffers wall time."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for x in r['presentation_samples']:
 if not x.get('native_transaction_candidate'):continue
 b=x['present_completion_boundary'];c=x['native_commit_stage_ns'];assert x['present_completion_barrier'] and c[0]<=b[0]<=b[1]<=c[6] and b[2]!=2**64-1
 rows.append(dict(display_index=x['display_index'],barrier_ms=(b[1]-b[0])/1e6,barrier_cycles=b[2],swap_ms=x['native_present_stage_ns'][1]/1e6))
assert rows
out=dict(checked=len(rows),median_barrier_ms=statistics.median(x['barrier_ms'] for x in rows),median_swap_ms=statistics.median(x['swap_ms'] for x in rows),long_barriers=sum(x['barrier_ms']>33.333333 for x in rows),long_swaps=sum(x['swap_ms']>33.333333 for x in rows),longest_barrier=sorted(rows,key=lambda x:x['barrier_ms'],reverse=True)[:8],longest_swap=sorted(rows,key=lambda x:x['swap_ms'],reverse=True)[:8],scope='CPU host-clock barrier and swap durations include OS/driver scheduling. glFinish confirms preceding GL completion, not physical scanout or exclusive GPU execution time.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
