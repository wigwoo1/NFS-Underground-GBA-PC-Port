from pathlib import Path
import json
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-face-read-reuse-20261006')
experiment={};exec(compile((cp/'candidates.experiment.py').read_text(),'road-experiment','exec'),experiment);road_candidates=experiment['road_candidates']
old={};exec(compile((cp/'candidates.before.py').read_text(),'road-baseline','exec'),old)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());results=[]
class Count:
 def __init__(self,inner):self.inner=inner;self.reads=0
 def read(self,address,size):
  if size==20:self.reads+=1
  return self.inner.read(address,size)
for row in r['wall_diagnostic_frames']:
 scene=ClosedGraph.decode(Path(row['graph']).read_bytes());a=Count(ClosedSceneMemory(scene,rom));b=Count(ClosedSceneMemory(scene,rom))
 baseline=old['road_candidates'](scene,a);candidate=road_candidates(scene,b)
 # Baseline classes are separately defined; compare every dataclass field.
 assert [vars(x) for x in baseline]==[vars(x) for x in candidate]
 assert a.inner.missing==b.inner.missing and b.reads<=a.reads
 results.append(dict(refresh=scene.refresh,candidates=len(candidate),before_face_reads=a.reads,after_face_reads=b.reads))
# Zero reduction is a valid negative optimization result.
(cp/'parity.json').write_text(json.dumps(dict(result='PASS',scenes=results,scope='Exact every-field candidate and missing-read parity across captured complete scenes; not performance or fullscene60fps proof'),indent=2))
print('PASS',len(results),'scenes',sum(x['before_face_reads'] for x in results),'to',sum(x['after_face_reads'] for x in results),'face reads')
