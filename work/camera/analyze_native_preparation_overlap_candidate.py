import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());preparation=r['world_preparation_stage_samples'];rows=r['presentation_samples'];assert preparation
for p in preparation:assert p['started_ns']<=p['constructed_ns']<=p['completed_ns']
ranked=sorted((x for x in rows if 'draw_end_ns' in x['callback_timing']),key=lambda x:x['callback_timing']['draw_end_ns']-x['callback_timing']['draw_begin_ns'],reverse=True)[:20]
checks=[]
for x in ranked:
 t=x['callback_timing'];a=t['draw_begin_ns'];b=t['draw_end_ns'];matches=[]
 for p in preparation:
  overlap=max(0,min(b,p['completed_ns'])-max(a,p['started_ns']))
  if overlap:matches.append(dict(older=p['older'],newer=p['newer'],overlap_ms=overlap/1e6,job_ms=(p['completed_ns']-p['started_ns'])/1e6,construct_cycles=p['construct_thread_cycles'],precompute_cycles=p['precompute_thread_cycles']))
 checks.append(dict(index=x['display_index'],draw_ms=(b-a)/1e6,source_ms=x.get('prepared',{}).get('source_prepare_ns',0)/1e6,stages=x.get('prepared',{}).get('consumer_stages'),preparation_overlap=matches))
durations=[(p['completed_ns']-p['started_ns'])/1e6 for p in preparation]
out=dict(result='PASS_CROSS_THREAD_INTERVAL_AUDIT',preparation_jobs=len(preparation),preparation_median_ms=statistics.median(durations),preparation_max_ms=max(durations),slowest_draws=checks,slowest_draws_with_overlap=sum(bool(x['preparation_overlap']) for x in checks),scope='Observed wall interval overlap of preparation and draw callbacks. Correlation only: does not prove GIL contention, CPU contention, causality or visible60fps. CPUthreadtime is quantized; cycles not CPUtime.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='slowest_draws'},indent=2))
for x in checks[:5]:print(x['index'],x['draw_ms'],[(p['older'],round(p['overlap_ms'],2),round(p['job_ms'],2)) for p in x['preparation_overlap']])
