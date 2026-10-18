"""Complete long API interval attribution; elapsed stages may overlap across threads."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];rows=ledger['records'];assert ledger['dropped']==0 and len(rows)==ledger['total'];assert r['gc_trace_dropped']==0
results=[]
for row in rows:
 assert row['interval_ns']==row['end_ns']-row['begin_ns'] and row['interval_ns']>33333000
 dispatch=row['renderer_dispatch'];caller=row['caller_stages'];stages=row['consumer_stages']
 assert dispatch['submitted_ns']<=dispatch['started_ns']<=dispatch['completed_ns']
 values={s['stage']:s['elapsed_ns']/1e6 for s in stages};assert all(v>=0 for v in values.values())
 work=dispatch['completed_ns']-dispatch['started_ns'];stage_sum=sum(s['elapsed_ns'] for s in stages);assert stage_sum<=work
 overlaps=[]
 for gc in r['gc_collection_samples']:
  a=max(row['begin_ns'],gc['start_ns']);b=min(row['end_ns'],gc['end_ns'])
  if a<b:overlaps.append((a,b))
 merged=[]
 for a,b in sorted(overlaps):
  if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
  else:merged.append((a,b))
 values.update(interval_ms=row['interval_ns']/1e6,renderer_queue_ms=(dispatch['started_ns']-dispatch['submitted_ns'])/1e6,renderer_work_ms=work/1e6,renderer_uninstrumented_ms=(work-stage_sum)/1e6,pair_to_slot_ms=(caller['slot_begin_ns']-caller['pair_begin_ns'])/1e6,present_ms=(row['present_end_ns']-row['present_begin_ns'])/1e6,gc_overlap_ms=sum(b-a for a,b in merged)/1e6)
 if 'pair_ready_ns' in caller:
  assert caller['pair_begin_ns']<=caller['pair_ready_ns']<=caller['slot_begin_ns']
  values['pair_setup_ms']=(caller['pair_ready_ns']-caller['pair_begin_ns'])/1e6
  values['after_pair_ready_ms']=(caller['slot_begin_ns']-caller['pair_ready_ns'])/1e6
 assert values['pair_to_slot_ms']>=0
 lease=row['hud_lease_stages']
 for label,a,b in [('hud_snapshot_ms','snapshot_begin_ns','snapshot_end_ns'),('hud_bind_ms','bind_begin_ns','callback_begin_ns'),('hud_callback_ms','callback_begin_ns','callback_end_ns'),('hud_release_ms','callback_end_ns','release_end_ns')]:
  assert lease[b]>=lease[a];values[label]=(lease[b]-lease[a])/1e6
 results.append(dict(display_index=row['display_index'],**values))
keys=results[0].keys()-{'display_index'}
out=dict(result='PASS_COMPLETE_LONG_INTERVAL_STAGE_AUDIT',count=len(rows),stats={k:dict(median=statistics.median(x[k] for x in results),max=max(x[k] for x in results)) for k in sorted(keys)},gc_overlap_count=sum(x['gc_overlap_ms']>0 for x in results),rows=results,scope='All recorded>33.333ms API intervals; stage elapsed can include scheduling/GIL/GC and overlap across threads. Uninstrumented remainder is dispatch elapsed minus sequential measured consumer stages, not exclusive CPU. pair_to_slot_ms includes earlier samples/pacing for the same pair and is not preparation cost; pair_setup_ms uses actual ready boundary when available. No causal or visible60fps claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
