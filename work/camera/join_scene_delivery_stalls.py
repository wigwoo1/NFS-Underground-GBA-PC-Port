"""Join observed stalls to recorded producer and preparation work, no causal claim."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());g=json.loads(Path(sys.argv[2]).read_text());rows={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')};out=[]
for gap in g['largest']:
 x=rows[gap['display_index']];prep=[p for p in r['world_preparation_stage_samples'] if (p['older'],p['newer'])==(x['source_older'],x['refresh']) and p['completed_ns']<=x['pair_ready_ns']]
 assert prep
 p=max(prep,key=lambda p:p['completed_ns'])
 producers=[p for p in r['producer_cycle_samples'] if p['refresh']==x['refresh'] and p['completed_ns']<=x['source_dequeued_ns']]
 start=x['native_committed_sample'][6]-int(round(gap['gap_ms']*1e6));end=x['source_dequeued_ns']
 updates=[u for u in r['original_update_samples'] if u['started_ns']<end and u['completed_ns']>start]
 producer=max(producers,key=lambda p:p['completed_ns']) if producers else None
 out.append(dict(display_index=x['display_index'],gap_ms=gap['gap_ms'],preparation=dict(unfinished_at_acquire_ms=max(0,p['completed_ns']-x['pair_begin_ns'])/1e6,completion_to_acquired_ms=(x['pair_ready_ns']-p['completed_ns'])/1e6,construct_ms=p['construct_advance_ns']/1e6,precompute_ms=p['precompute_ns']/1e6),producer=producer,overlapping_original_updates=[dict(refresh=u['refresh'],wall_ms=(u['completed_ns']-u['started_ns'])/1e6,thread_cycles=u['thread_cycles'],started_late_ms=(u['started_ns']-u['original_deadline_ns'])/1e6) for u in updates]))
result=dict(result='PASS_PRODUCER_PREPARATION_JOIN',gaps=len(out),largest=out,scope='Recorded wall/cycle intervals, not exclusive CPU attribution. Producer/update/preparation can overlap; do not sum across threads. No CPU-load observation or physical scanout proof.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(dict(gaps=len(out),largest=out[:2]),indent=2))
