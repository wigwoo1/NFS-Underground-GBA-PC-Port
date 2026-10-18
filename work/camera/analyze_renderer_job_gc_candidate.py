"""Renderer-job GC intersections and nonadditive native/consumer detail."""
import json,sys
from pathlib import Path
def analyze(r):
 ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']
 assert ledger['dropped']==0 and r['gc_trace_dropped']==0
 rows=[]
 for event in ledger['records']:
  prepared=event['prepared'];d=prepared['renderer_dispatch']
  a,b=d['started_ns'],d['completed_ns'];assert a<=b and d['kind']=='prepare'
  overlaps=[]
  for g in r['gc_collection_samples']:
   assert g['start_ns']<=g['end_ns']
   span=max(0,min(b,g['end_ns'])-max(a,g['start_ns']))
   if span:overlaps.append(dict(generation=g['generation'],thread=g['thread_id'],renderer_thread=g['thread_id']==d['thread'],overlap_ms=span/1e6,duration_ms=(g['end_ns']-g['start_ns'])/1e6))
  stages={s['stage']:s['elapsed_ns']/1e6 for s in prepared['consumer_stages']}
  assert len(stages)==len(prepared['consumer_stages'])
  rows.append(dict(index=event['display_index'],renderer_job_ms=(b-a)/1e6,source_prepare_ms=prepared['source_prepare_ns']/1e6,consumer_stage_ms=stages,gc_intersections=overlaps,hud_lease=prepared.get('hud_lease_stages'),native_calls=prepared.get('d3d_call_profiles'),bundle_transfer=prepared.get('bundle_transfer_profile'),scope='Native calls/HUD profile nested; wall/cycles do not equal CPU time. Other-thread GC intersection may block Python globally but is not exclusive cause proof.'))
 return dict(result='PASS_RENDERER_JOB_GC_INTERSECTIONS',rows=sorted(rows,key=lambda x:x['renderer_job_ms'],reverse=True),scope='Complete retained long native gaps with zero-drop parent GC ledger; measured renderer wall time and nested substages.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()))
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
 print(out['result'])
 for x in out['rows'][:3]:print(x['index'],x['renderer_job_ms'],x['source_prepare_ms'],x['consumer_stage_ms'],x['gc_intersections'])
