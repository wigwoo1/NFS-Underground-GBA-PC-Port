import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['presentation_samples'];assert rows
pairs={};samples=[]
for row in rows:
 c=row['caller_stages'];begin=c['pair_begin_ns'];ready=c['pair_ready_ns'];slot=c['slot_begin_ns'];take_a=c['preparation_take_begin_ns'];take_b=c['preparation_take_end_ns'];hud_a=c['hud_prefetch_wait_begin_ns'];hud_b=c['hud_prefetch_wait_end_ns']
 assert begin<=take_a<=take_b<=hud_a<=hud_b<=ready<=slot
 key=(row['epoch'],row['generation'],row['source_older'],row['refresh'])
 signature=(begin,ready,take_a,take_b,hud_a,hud_b)
 assert key not in pairs or pairs[key]==signature;pairs[key]=signature
 samples.append(dict(display_index=row['display_index'],pair_setup_ms=(ready-begin)/1e6,world_take_ms=(take_b-take_a)/1e6,hud_future_wait_ms=(hud_b-hud_a)/1e6,after_pair_ready_ms=(slot-ready)/1e6,previous_pair_to_slot_ms=(slot-begin)/1e6))
 assert (slot-begin)==(ready-begin)+(slot-ready)
out=dict(result='PASS_PAIR_READY_CHRONOLOGY',retained_samples=len(rows),retained_pairs=len(pairs),max_pair_setup_ms=max(x['pair_setup_ms'] for x in samples),max_hud_future_wait_ms=max(x['hud_future_wait_ms'] for x in samples),max_accumulated_after_ready_ms=max(x['after_pair_ready_ms'] for x in samples),scope='Retained presentation window only. Pair-ready boundary shared across every sample of each exact scene pair; prior pair-to-slot includes earlier samples and pacing, so is not setup CPU cost.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
