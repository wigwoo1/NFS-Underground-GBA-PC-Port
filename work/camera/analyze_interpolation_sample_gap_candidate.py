"""Exact pre-draw partition from complete native commit gap ledger."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text())
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']
assert ledger['dropped']==0
rows=[]
for event in ledger['records']:
 c=event['caller_stages'];begin=event['begin_ns'];draw=event['caller_timing']['draw_begin_ns']
 keys=['slot_begin_ns','sample_end_ns','sky_begin_ns','sky_end_ns','owner_begin_ns','owner_end_ns','lock_begin_ns','lock_acquired_ns']
 raw=[c[k] for k in keys]
 assert raw==sorted(raw) and raw[-1]<=draw
 # A retained pair may predate prior commit; clip the slot start only when necessary.
 stamps=[begin]+[max(begin,x) for x in raw]+[draw]
 assert stamps==sorted(stamps)
 names=['before_slot','sample_retrieval','sample_to_sky','sky_sample','sky_to_owner','owner_construct','owner_to_lock','publication_lock_wait','lock_to_draw']
 values=[(b-a)/1e6 for a,b in zip(stamps,stamps[1:])]
 assert sum(b-a for a,b in zip(stamps,stamps[1:]))==draw-begin
 rows.append(dict(identity=[event['epoch'],event['generation'],event['display_index']],gap_ms=event['interval_ns']/1e6,pre_draw_ms=(draw-begin)/1e6,partition_ms=dict(zip(names,values))))
out=dict(result='PASS_COMPLETE_INTERPOLATION_SAMPLE_GAP_PARTITION',rows=rows,scope='Exact elapsed pre-draw partition for every retained native long gap with zero drops. sample_retrieval includes pair condition lock and synchronous sample readiness wait, not exclusive CPU. No visible cadence claim.')
p.with_name(p.stem+'-interpolation-sample-gap.json').write_text(json.dumps(out,indent=2));print(out['result']);print(rows)
