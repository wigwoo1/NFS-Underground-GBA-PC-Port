"""Audit sky draw intervals without treating coarse CPU zeros as exact zeros."""
import json,sys,statistics
from pathlib import Path

def analyze(d):
 rows=[r for r in d['presentation_samples'] if r.get('sky_interpolated') and r.get('native_draw_elapsed_ns') is not None]
 paired=[r for r in rows if r.get('gpu_timer_async') and r.get('gpu_elapsed_ns') is not None]
 def item(r):
  cpu=r.get('native_draw_thread_cpu_ns');elapsed=r['native_draw_elapsed_ns']
  return dict(display_index=r['display_index'],elapsed_ms=elapsed/1e6,thread_cpu_ms=cpu/1e6 if cpu is not None else None,gpu_ms=r.get('gpu_elapsed_ns')/1e6 if r.get('gpu_elapsed_ns') is not None else None,gpu_query_started=bool(r.get('gpu_timer_async')),elapsed_minus_cpu_ms=(elapsed-cpu)/1e6 if cpu is not None else None)
 return dict(scope='Elapsed intervals include driver waits and descheduling. Windows thread CPU values are coarse; zero is not proof of no CPU work. GPU queries cover queued draw commands, not display scanout. Sequential timings do not establish causality.',sky_draws=len(rows),completed_gpu_queries=len(paired),worst_elapsed=[item(r) for r in sorted(rows,key=lambda r:r['native_draw_elapsed_ns'],reverse=True)[:10]],slow_with_gpu=[item(r) for r in sorted(paired,key=lambda r:r['native_draw_elapsed_ns'],reverse=True)[:10]],gpu_median_ms=statistics.median(r['gpu_elapsed_ns']/1e6 for r in paired) if paired else None,gpu_max_ms=max((r['gpu_elapsed_ns']/1e6 for r in paired),default=None))
if __name__=='__main__':
 p=Path(sys.argv[1]);result=analyze(json.loads(p.read_text()));p.with_suffix('.sky-draw-waits.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
