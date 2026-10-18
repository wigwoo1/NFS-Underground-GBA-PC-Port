"""Compare GPU command intervals with CPU query submission envelopes."""
import json,sys,statistics
from pathlib import Path
def analyze(r):
 rows=[]
 for x in r['presentation_samples']:
  if x.get('gpu_elapsed_ns') is None:continue
  assert x['gpu_timer_async'] and x['gpu_query_begin_ns'] is not None and x['gpu_query_end_ns'] is not None
  assert x['sample_begin_ns']<=x['gpu_query_begin_ns']<=x['draw_complete_ns']
  assert x['gpu_query_begin_ns']<=x['gpu_query_end_ns']<=x['draw_complete_ns']
  assert x['native_committed_sample'] and x['native_wait_timing'] and x['input_draw_batched']
  cpu=(x['gpu_query_end_ns']-x['gpu_query_begin_ns'])/1e6;gpu=x['gpu_elapsed_ns']/1e6
  rows.append(dict(index=x['display_index'],older=x['source_older'],newer=x['refresh'],gpu_interval_ms=gpu,cpu_envelope_ms=cpu,draw_wall_ms=x['draw_cpu_ns']/1e6,swap_ms=x['native_present_stage_ns'][1]/1e6))
 assert rows
 return dict(scope='CPU envelope is host submission elapsed time; GPU query spans command processing including possible starvation/driver waits. Their clocks are different and intervals are not exclusive utilization or scanout proof.',samples=len(rows),gpu_median_ms=statistics.median(x['gpu_interval_ms'] for x in rows),cpu_median_ms=statistics.median(x['cpu_envelope_ms'] for x in rows),gpu_over100ms=sum(x['gpu_interval_ms']>=100 for x in rows),gpu_exceeds_cpu_by_refresh=sum(x['gpu_interval_ms']>x['cpu_envelope_ms']+1000/60 for x in rows),largest=sorted(rows,key=lambda x:x['gpu_interval_ms'],reverse=True)[:12])
if __name__=='__main__':
 p=Path(sys.argv[1]);a=analyze(json.loads(p.read_text()));p.with_suffix('.gpu-envelope.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
