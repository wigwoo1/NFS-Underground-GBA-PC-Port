import json,sys,statistics
from pathlib import Path
from analyze_active_play_cadence import analyze
def summary(path):
 r=json.loads(Path(path).read_text())
 def stats(v):
  s=sorted(v);return dict(count=len(s),median=statistics.median(s),p95=s[min(len(s)-1,int(.95*len(s)))],maximum=max(s)) if s else None
 return dict(report=str(path),cadence=analyze(r),producer_ms=stats([x['ns']/1e6 for x in r['producer_cycle_samples']]),graph_decode_match_ms=stats([x['stages']['graph_decode_match_ns']/1e6 for x in r['producer_cycle_samples']]),precompute_ms=stats([x['precompute_ns']/1e6 for x in r['world_preparation_stage_samples'] if not x.get('history_only')]))
result=dict(candidate=summary(sys.argv[1]),baseline=summary(sys.argv[2]),scope='Same flags/route duration, sequential runs with externally uncontrolled CPU load. No causal benefit or physical scanout proof.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
