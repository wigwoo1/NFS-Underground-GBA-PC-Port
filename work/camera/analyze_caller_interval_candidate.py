"""Attribute long interval overlap to measured caller and native wait windows."""
import json,sys
from pathlib import Path
from analyze_long_interval_partition_candidate import union_ns
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0
pairs={'preparation_take':('preparation_take_begin_ns','preparation_take_end_ns'),'sample':('slot_begin_ns','sample_end_ns'),'sky':('sky_begin_ns','sky_end_ns'),'owner':('owner_begin_ns','owner_end_ns'),'publication_lock':('lock_begin_ns','lock_acquired_ns')}
rows=[]
for e in ledger['records']:
    c=e['caller_stages'];assert c is not None
    begin,end=e['begin_ns'],e['end_ns'];windows=[];costs={}
    for name,(a,b) in pairs.items():
        assert c[b]>=c[a];w=(c[a],c[b]);windows.append(w);costs[name]=union_ns([w],begin,end)/1e6
    assert e['transaction_end_ns']>=e['transaction_begin_ns']
    tx=(e['transaction_begin_ns'],e['transaction_end_ns']);windows.append(tx)
    callbacks=[(e['draw_begin_ns'],e['draw_end_ns']),(e['present_begin_ns'],e['present_end_ns'])]
    tx_ns=union_ns([tx],begin,end);cb_ns=union_ns(callbacks,begin,end)
    assert tx_ns>=cb_ns
    costs['transaction_outside_callbacks']=(tx_ns-cb_ns)/1e6
    costs['transaction_total']=tx_ns/1e6
    costs['uncovered_by_caller_and_transaction']=(end-begin-union_ns(windows,begin,end))/1e6
    rows.append(dict(index=e['display_index'],interval_ms=e['interval_ns']/1e6,overlap_ms=costs))
out=dict(result='LONG_CALLER_STAGE_OVERLAP',total=len(rows),rows=sorted(rows,key=lambda x:x['interval_ms'],reverse=True),scope='Wall-clock windows clipped to observed API interval. Transaction residual includes native pacing and callback transition overhead; caller stages can overlap GC. No exclusive cause or scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['total']);print(out['rows'][:5])
