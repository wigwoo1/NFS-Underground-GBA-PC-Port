from pathlib import Path
import re,json,statistics,sys
p=Path(sys.argv[1])
rows=[dict(re.findall(r'(\w+)=([-\d.]+)',line)) for line in Path(str(p)+'-host.log').read_text().splitlines() if line.startswith('motion_capture_profile ')]
accepted=[r for r in rows if r['accepted']=='1'];assert accepted
out=dict(result='RETAINED_MOTION_CAPTURE_STAGE_COSTS',prefix=str(p),attempts=len(rows),accepted=len(accepted),stages={})
for k in ('acquire','scene_rebuild','initial_owner','root_commands','road_assets','reserved','complete_clone','total'):
 v=sorted(float(r[k]) for r in accepted);out['stages'][k]=dict(sum_ms=sum(v),median_ms=statistics.median(v),p95_ms=v[int((len(v)-1)*.95)],max_ms=max(v))
out['scope']='Existing producer wall instrumentation, accepted motion only; scene_rebuild and initial_owner partition geometry_owner, do not add parent stage twice.'
Path(str(p)+'-capture-stage-analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
