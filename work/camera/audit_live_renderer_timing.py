"""Report actual clock progress and renderer costs; completion alone is not a timing pass."""
import json,sys,statistics
from pathlib import Path

def summarize(path):
 r=json.loads(Path(path).read_text()); t=r['timing']; samples=r.get('presentation_samples',[])
 out={'report':str(path),'result':r['result'],'original_updates':r['original_updates'],'presentations':r['presentations'],'simulation_to_wall_ratio':t['simulated_seconds']/t['wall_seconds'],'smooth_60fps_verified':False}
 for key in ('gpu_completion_wait_ns','draw_cpu_ns','pair_prepare_ns'):
  values=sorted(s[key]/1e6 for s in samples if s.get(key) is not None)
  if values:out[key]={'count':len(values),'median_ms':statistics.median(values),'p95_ms':values[min(len(values)-1,int(len(values)*.95))],'max_ms':max(values),'total_ms':sum(values)}
 deadlines=[(s['present_end_ns']-s['presentation_deadline_ns'])/1e6 for s in samples if s.get('presentation_deadline_ns') is not None]
 if deadlines:out['deadline_lateness']={'count':len(deadlines),'over_one_display_interval':sum(v>1000/60 for v in deadlines),'max_ms':max(deadlines)}
 return out
if __name__=='__main__':
 for path in sys.argv[1:]:print(json.dumps(summarize(path),indent=2))
