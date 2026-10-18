"""Associate complete original-update execution with native commit gaps."""
import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
p=Path(sys.argv[1]);r=json.loads(p.read_text());analyze(r)
ledger=r['original_update_retention']['complete_original_updates'];updates=ledger['records']
assert ledger['dropped']==0 and ledger['total']==len(updates)==r['original_updates']
assert all(b['refresh']==a['refresh']+1 for a,b in zip(updates,updates[1:]))
by={x['refresh']:x for x in updates};assert len(by)==len(updates)
for x in updates:
 a,b,*_=x['native_boundary'];assert x['started_ns']<=a<=b<=x['completed_ns']
rows=[]
for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 start,end=e['begin_ns'],e['end_ns'];refresh=e['transaction']['commit'][3];assert refresh in by
 overlaps=[]
 for x in updates:
  a,b,cycles,*_=x['native_boundary'];lo=max(start,a);hi=min(end,b)
  if hi>lo:overlaps.append(dict(refresh=x['refresh'],native_overlap_ms=(hi-lo)/1e6,native_elapsed_ms=(b-a)/1e6,native_thread_cycles=cycles))
 source=by[refresh]
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],source_newer=refresh,gap_ms=(end-start)/1e6,source_update_completion_relative_prior_commit_ms=(source['completed_ns']-start)/1e6,source_update_native_ms=(source['native_boundary'][1]-source['native_boundary'][0])/1e6,original_native_overlap_ms=sum(x['native_overlap_ms'] for x in overlaps),overlapping_updates=overlaps))
out=dict(result='PASS_COMPLETE_UPDATE_NATIVE_GAP_OVERLAP',updates=len(updates),rows=sorted(rows,key=lambda x:x['gap_ms'],reverse=True),scope='Complete contiguous original-update ledger and zero-drop long native commit gaps. Concurrent native elapsed overlap is association only, not exclusive CPU contention or causal stall proof; thread cycles not converted to time.')
p.with_name(p.stem+'-complete-update-gap-overlap.json').write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps(out['rows'][:3],indent=2))
