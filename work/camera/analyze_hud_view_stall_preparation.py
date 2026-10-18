import json,collections
from pathlib import Path
report=Path('work/camera/prototype-runs/owned-native-1791411569465834300.json')
r=json.loads(report.read_text());results=[]
for x in r['world_preparation_stage_samples']:
 if (x['older'],x['newer']) not in ((8805,8808),(10316,10321)):continue
 samples=[]
 for sample in x['sample_timings']:
  assembly=[dict(name=s['name'],wall_ms=s['wall_ns']/1e6,cycles=s.get('thread_cycles')) for s in sample.get('assembly_stages',[])]
  source=[dict(name=s['name'],wall_ms=s['wall_ns']/1e6) for s in sample.get('source_sample_stages',[])]
  samples.append(dict(alpha=sample['alpha'],wall_ms=sample['wall_ns']/1e6,assembly=assembly,source=source))
 results.append(dict(started_ns=x['started_ns'],completed_ns=x['completed_ns'],history_only=x['history_only'],older=x['older'],newer=x['newer'],construct_ms=x['construct_advance_ns']/1e6,precompute_ms=x['precompute_ns']/1e6,construct=[dict(name=s['name'],wall_ms=s['wall_ns']/1e6) for s in x['construct_stages']],samples=samples))
assert {(x['older'],x['newer']) for x in results}=={(8805,8808),(10316,10321)}
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-view-stall-preparation-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='ATTRIBUTED_STAGE_TIMES',intervals=results,scope='Recorded overlapping preparation intervals; nested times not summed as exclusive costs. Wall time includes scheduling. Not a causal stall proof.'),indent=2))
(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print('PASS recorded preparation records',len(results))


