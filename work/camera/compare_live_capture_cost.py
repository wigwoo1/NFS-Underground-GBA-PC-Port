from pathlib import Path
import json,re,statistics
p=Path(__file__).resolve().parent;latest=json.loads((p/'threaded-racing-motion-audit.json').read_text());baseline=json.loads((p.parent.parent/'outputs/nfsug-native-renderer/camera-research/lifecycle/sampled-alpha-live-readback-milestone-20261005T124127Z/threaded-racing-motion-audit.json').read_text());result=[]
for label,report in [('copied',baseline),('shared_profiled',latest)]:
 log=Path(report['prefix']+'-host.log').read_text();rows=[dict((k,float(v)) for k,v in re.findall(r'(\w+)=([0-9.]+)',line)) for line in log.splitlines() if line.startswith('motion_capture_profile ')]
 costs={k:dict(median_ms=statistics.median([r[k] for r in rows if k in r]),total_ms=sum(r[k] for r in rows if k in r)) for k in ['acquire','scene_rebuild','root_commands','road_assets','complete_clone','total'] if rows}
 result.append(dict(mode=label,captures=len(rows),accepted=sum(r.get('accepted',0)==1 for r in rows),costs=costs,original_tick_timing=report['original_tick_timing']))
output=dict(result='CAPTURE_COST_COMPONENT_COMPARISON',runs=result,scope='One instrumented run per mode; differing progress and scheduling. No speedup claim; fullscene60fps not verified.')
(p/'live-motion-capture-cost-comparison.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
