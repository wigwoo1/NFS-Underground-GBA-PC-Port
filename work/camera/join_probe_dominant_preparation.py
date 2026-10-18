import json
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/frame-comparison-live-20261008');r=json.loads(Path('work/camera/prototype-runs/owned-native-1791433570608812300.json').read_text());j=json.loads((p/'presentation-gap-join.json').read_text());rows={x['display_index']:x for x in r['presentation_samples'] if 'display_index' in x}
checks=[]
for g in j['largest'][:3]:
 x=rows[g['display_index']];candidates=[s for s in r['world_preparation_stage_samples'] if s['older']==x['source_older'] and s['newer']==x['refresh'] and s['completed_ns']<=x['pair_ready_ns']];assert candidates
 s=max(candidates,key=lambda s:s['completed_ns'])
 checks.append(dict(display_index=g['display_index'],older=s['older'],newer=s['newer'],unfinished_at_acquire_ms=max(0,s['completed_ns']-x['pair_begin_ns'])/1e6,completion_to_acquired_ms=(x['pair_ready_ns']-s['completed_ns'])/1e6,stages=s))
(p/'dominant-preparation-join.json').write_text(json.dumps(dict(checks=checks,scope='Same captured preparation pair, completion precedes acquisition. Stage wall times include scheduling.'),indent=2));print(json.dumps([{k:v for k,v in c.items() if k!='stages'} for c in checks],indent=2))

