"""Attribute only comparison wall-time overlapping actual presentation gaps."""
import json,sys
from pathlib import Path
from analyze_consumer_gap_partition import analyze
rp,lp,op=map(Path,sys.argv[1:4]);r=json.loads(rp.read_text());ledger=json.loads(lp.read_text());part=analyze(r)
rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample')];pairs={b['display_index']:(a,b) for a,b in zip(rows,rows[1:])}
for gap in part['largest']:
 a,b=pairs[gap['display_index']];start=a['native_committed_sample'][6];end=b['native_committed_sample'][6]
 matching=[x for x in ledger['records'] if x['frame_identity']==[b['refresh'],b['epoch']] and b['source_dequeued_ns']<=x['start_ns']<=x['end_ns']<=b['pair_begin_ns']]
 assert len(matching)==1,(b['display_index'],len(matching))
 p=matching[0];overlap=max(0,min(end,p['end_ns'])-max(start,p['start_ns']))/1e6
 gap['comparison']=dict(refresh=b['refresh'],probe_ms=p['wall_ns']/1e6,overlap_ms=overlap,thread_cycles=p['thread_cycles'],fraction_of_gap=overlap/gap['gap_ms'])
result=dict(result='PASS_OVERLAP_JOIN',gaps=len(part['largest']),largest=part['largest'],scope='Exact retained sample identity and disjoint comparison overlap, not summing nested intervals. Excludes pause-crossing gaps per partition. Diagnostic timing, no exclusive cause or scanout claim.')
op.write_text(json.dumps(result,indent=2));print(json.dumps(result['largest'][:3],indent=2))
