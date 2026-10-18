from pathlib import Path
import cProfile,pstats,json
from owned_closed_scene_memory import ClosedSceneMemory
from owned_road_material_decode_reuse_candidate import candidate
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns);env=ns['env'];scenes=env['scenes'];memories=[ClosedSceneMemory(s.graph,env['rom']) for s in scenes]
profile=cProfile.Profile();profile.enable()
for _ in range(256):
 for scene,memory in zip(scenes,memories):candidate(scene.graph,memory)
profile.disable();stats=pstats.Stats(profile);rows=[]
for (file,line,name),(primitive,calls,own,total,callers) in stats.stats.items():rows.append(dict(file=file,line=line,function=name,calls=calls,own_seconds=own,cumulative_seconds=total))
rows.sort(key=lambda r:r['own_seconds'],reverse=True)
out=dict(result='PROFILED_CURRENT_WORKER_ROAD_DECODER',endpoint_decodes=512,rows=rows[:18],scope='cProfile perturbs timing; attributes current installed material-cache decoder on two actual endpoints. Not live cadence or absolute performance qualification.')
Path('outputs/nfsug-native-renderer/camera-research/current-road-decoder-profile-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(rows[:7],indent=2))
