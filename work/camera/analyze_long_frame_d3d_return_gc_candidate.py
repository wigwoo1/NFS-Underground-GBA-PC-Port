import json,statistics
from pathlib import Path
raw=json.loads(Path('work/camera/prototype-runs/owned-native-1791539421523885700.json').read_text());profile=json.loads(Path('work/camera/prototype-runs/native-callback-cycles-20261009.json').read_text());mapping={(x['epoch'],x['generation'],x['index']):x for x in profile['rows']};ledger=raw['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and len(ledger['records'])==ledger['total'];assert raw['gc_trace_dropped']==0
stats={};rows=[]
def overlap(a,b,thread=None):
 intervals=[]
 for g in raw['gc_collection_samples']:
  if thread is not None and g['thread_id']!=thread:continue
  lo=max(a,g['start_ns']);hi=min(b,g['end_ns'])
  if lo<hi:intervals.append((lo,hi))
 merged=[]
 for lo,hi in sorted(intervals):
  if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
  else:merged.append((lo,hi))
 return sum(hi-lo for lo,hi in merged)/1e6
for record in ledger['records']:
 session=mapping[(record['epoch'],record['generation'],record['display_index'])];calls=[]
 for call in record['d3d_call_profiles']+[dict(record['bundle_transfer_profile'],call='bundle_transfer')]:
  a,b,c,d=[call[k] for k in ('caller_begin_ns','native_begin_ns','native_end_ns','caller_end_ns')];assert a<=b<=c<=d
  row=dict(call=call['call'],caller_ms=(d-a)/1e6,native_ms=(c-b)/1e6,before_native_ms=(b-a)/1e6,after_native_ms=(d-c)/1e6,native_cycles=call['native_cycles'],after_native_gc_overlap_ms=overlap(c,d),after_native_owner_gc_overlap_ms=overlap(c,d,session['thread']))
  calls.append(row);stats.setdefault(row['call'],[]).append(row)
 h=record['hud_lease_stages'];rows.append(dict(index=record['display_index'],session_ms=(session['end_ns']-session['begin_ns'])/1e6,session_gc_overlap_ms=overlap(session['begin_ns'],session['end_ns']),session_owner_gc_overlap_ms=overlap(session['begin_ns'],session['end_ns'],session['thread']),hud_snapshot_ms=(h['snapshot_end_ns']-h['snapshot_begin_ns'])/1e6,calls=calls))
result=dict(result='PASS_LONG_FRAME_D3D_RETURN_GC_JOIN',count=len(rows),medians={name:{k:statistics.median(x[k] for x in values) for k in values[0] if k!='call'} for name,values in stats.items()},session_gc_median_ms=statistics.median(x['session_gc_overlap_ms'] for x in rows),session_owner_gc_median_ms=statistics.median(x['session_owner_gc_overlap_ms'] for x in rows),snapshot_median_ms=statistics.median(x['hud_snapshot_ms'] for x in rows),rows=rows,scope='Exact17longframe identity join; native/caller nesting and clipped completeGCunion. GC includes all traced threads, temporal overlap is not exclusivecause. After-native gap can include GIL reacquisition/scheduling/FFI but does not independently distinguish them.')
Path('work/camera/prototype-runs/long-frame-d3d-return-gc-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
