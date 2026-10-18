"""Complete long-frame packet return/GC overlap; no exclusive-cause inference."""
import json,sys,statistics
from pathlib import Path
raw=json.loads(Path(sys.argv[1]).read_text())
assert raw['result']=='SMOKE_COMPLETE' and raw['error'] is None
assert raw['gc_trace_dropped']==0
ledger=raw['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
assert ledger['dropped']==0 and len(ledger['records'])==ledger['total']
def overlap(a,b):
 intervals=[]
 for g in raw['gc_collection_samples']:
  assert g['start_ns']<=g['end_ns']
  lo=max(a,g['start_ns']);hi=min(b,g['end_ns'])
  if lo<hi:intervals.append((lo,hi))
 merged=[]
 for lo,hi in sorted(intervals):
  if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
  else:merged.append((lo,hi))
 return sum(hi-lo for lo,hi in merged)
rows=[];identities=set()
for x in ledger['records']:
 identity=(x['epoch'],x['generation'],x['display_index']);assert identity not in identities;identities.add(identity)
 call=x['bundle_transfer_profile'];a,b,c,d=[call[k] for k in ('caller_begin_ns','native_begin_ns','native_end_ns','caller_end_ns')]
 assert a<=b<=c<=d
 dispatch=x['renderer_dispatch'];assert dispatch['started_ns']<=a<=d<=dispatch['completed_ns']
 gc=overlap(c,d);assert 0<=gc<=d-c
 rows.append(dict(epoch=identity[0],generation=identity[1],index=identity[2],native_ms=(c-b)/1e6,after_return_ms=(d-c)/1e6,gc_overlap_ms=gc/1e6,non_gc_elapsed_ms=(d-c-gc)/1e6,interval_ms=x['interval_ns']/1e6))
out=dict(result='PASS_COMPLETE_PACKET_RETURN_GC_JOIN',count=len(rows),rows=rows,max_after_return=max(rows,key=lambda x:x['after_return_ms']),median_after_return_ms=statistics.median(x['after_return_ms'] for x in rows),scope='Complete long API frame ledger only. Clipped union of all traced GC intervals, not exclusive CPU/scheduling attribution; no Python owner thread assumption from native thread IDs.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
