"""Report asynchronous GPU timing coverage, including missing slow-swap observations."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=[]
for x in r['presentation_samples']:
 stages=x.get('native_present_stage_ns')
 if stages is None:continue
 rows.append(dict(refresh=x['refresh'],index=x['display_index'],swap_ms=stages[1]/1e6,gpu_ms=None if x.get('gpu_elapsed_ns') is None else x['gpu_elapsed_ns']/1e6,query_started=bool(x.get('gpu_timer_async')),native_draw_ms=x.get('native_draw_elapsed_ns',0)/1e6))
assert rows
matched=[x for x in rows if x['gpu_ms'] is not None];slow=[x for x in rows if x['swap_ms']>33.333]
out=dict(scope='Asynchronous elapsed queries cover selected draws, not swaps or scanout; missing values must not be imputed',presentations=len(rows),measured_gpu_draws=len(matched),unmeasured=len(rows)-len(matched),slow_swaps=len(slow),slow_swaps_measured_gpu=sum(x['gpu_ms'] is not None for x in slow),gpu_median_ms=statistics.median(x['gpu_ms'] for x in matched),gpu_max_ms=max(x['gpu_ms'] for x in matched),largest_measured=sorted(matched,key=lambda x:x['gpu_ms'],reverse=True)[:8],largest_swaps=sorted(rows,key=lambda x:x['swap_ms'],reverse=True)[:8],pending=r.get('gpu_timer_pending'),skipped=r.get('gpu_timer_skipped'))
p.with_suffix('.gpu-swap-coverage.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
