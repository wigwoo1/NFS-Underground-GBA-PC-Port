import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for g in ledger['records']:
 w=g['native_wait'];assert len(w)==4 and all(type(v) is int for v in w) and w[2]>=w[1]
 assert w[1]==g['presentation_deadline_ns']
 stamps=[g['transaction_begin_ns'],g['draw_begin_ns'],g['draw_end_ns'],w[0],w[2],g['present_begin_ns'],g['present_end_ns'],g['transaction_end_ns']]
 assert all(a<=b for a,b in zip(stamps,stamps[1:]))
 names=['before_draw_ms','draw_ms','draw_to_wait_ms','native_wait_ms','wait_to_present_ms','present_ms','after_present_ms']
 parts={n:(b-a)/1e6 for n,a,b in zip(names,stamps,stamps[1:])};assert abs(sum(parts.values())-(stamps[-1]-stamps[0])/1e6)<1e-8
 stages=g['native_commit_stages'];assert len(stages)==7 and all(a<=b for a,b in zip(stages,stages[1:]))
 rows.append(dict(index=g['display_index'],api_interval_ms=g['interval_ns']/1e6,requested_remaining_ms=max(0,w[1]-w[0])/1e6,deadline_overshoot_ms=max(0,w[2]-max(w[0],w[1]))/1e6,sleeps=w[3],**parts))
out=dict(result='PASS_COMPLETE_NATIVE_WAIT_TRANSACTION_PARTITION',rows=sorted(rows,key=lambda x:x['deadline_overshoot_ms'],reverse=True),scope='Exact native wait deadline/return and complete transaction elapsed partitions for all retained gaps. Overshoot includes scheduling; not exclusive timer cause or smooth60 proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
