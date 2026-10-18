"""Compare complete-renderer timing reports without claiming controlled performance or scanout."""
import json,statistics,sys
from pathlib import Path
out=[]
for name in sys.argv[1:3]:
 r=json.loads(Path(name).read_text());a=[x for x in r['presentation_samples'] if x.get('native_batch_candidate')];assert a
 def med(key):return statistics.median(key(x) for x in a)
 out.append(dict(report=name,swap_requested=r['swap_interval_requested'],swap_observed=r['swap_interval_observed'],updates=r['original_updates'],scenes=r['owned_scene_submissions'],presentations=r['presentations'],samples=len(a),median_swap_ms=med(lambda x:x['native_present_stage_ns'][1]/1e6),median_completion_lateness_ms=med(lambda x:(x['present_end_ns']-x['presentation_deadline_ns'])/1e6),first_120_median_lateness_ms=statistics.median((x['present_end_ns']-x['presentation_deadline_ns'])/1e6 for x in a[:120]),last_120_median_lateness_ms=statistics.median((x['present_end_ns']-x['presentation_deadline_ns'])/1e6 for x in a[-120:])))
result=dict(reports=out,scope='Sequential uncontrolled runs, identical complete renderer and smoke options except swap interval. CPU timestamps only; interval0 may tear and is not final smooth display solution.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
