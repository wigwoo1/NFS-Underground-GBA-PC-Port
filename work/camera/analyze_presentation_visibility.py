"""Compare shown/hidden runs without claiming causal or scanout proof."""
import json,sys
from pathlib import Path
from analyze_active_play_cadence import analyze

def summarize(p):
 r=json.loads(Path(p).read_text());rows=[x for x in r['presentation_samples'] if x.get('hidden_window_presented') and x.get('native_present_stage_ns')]
 assert rows
 for x in rows:
  a=x['native_commit_stage_ns'];b=x['native_present_stage_ns'];assert all(z>=0 for z in b) and sum(b)<=a[4]-a[3]
 return dict(report=str(p),result=r['result'],window_shown=r['window_shown'],measured_frames=len(rows),original_updates=r['original_updates'],swap_interval=r['swap_interval_observed'],swap_max_ms=max(x['native_present_stage_ns'][1] for x in rows)/1e6,swap_over_refresh=sum(x['native_present_stage_ns'][1]>1e9/60 for x in rows),cadence=analyze(r),clean_shutdown=not r['shutdown_evidence']['gpu_thread_alive'] and not r['shutdown_evidence']['preparation_thread_alive'] and r['shutdown_evidence']['active_contexts_after_close']==0,scope='Shown flag proves requested ShowWindow path; foreground, occlusion and physical scanout not measured. Sequential runs can differ in host scheduling.')
if __name__=='__main__':print(json.dumps([summarize(p) for p in sys.argv[1:]],indent=2))
