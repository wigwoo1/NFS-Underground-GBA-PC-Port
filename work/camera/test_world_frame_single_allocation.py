"""Exact complete-scene assembler parity against saved pre-optimization source."""
import runpy,json
from pathlib import Path
import owned_prepared_world_motion as motion
checkpoint=Path('outputs/nfsug-native-renderer/camera-research/lifecycle/world-frame-single-allocation-20261006')
reference={};exec(compile((checkpoint/'before-assembler.py').read_text(),'reference_assembler','exec'),reference)
candidate=motion.assemble_world;count=0
def compare(*args):
 global count
 old=reference['assemble_world'](*args);new=candidate(*args)
 assert old[0]==new[0] and old[4]==new[4]
 for a,b in zip(old[1:4],new[1:4]):assert (a is None and b is None) or bytes(a)==bytes(b)
 count+=1;return new
motion.assemble_world=compare
try:runpy.run_path('work/camera/test_external_fullscene_transition.py')
finally:motion.assemble_world=candidate
result=dict(exact_complete_samples=count,scope='framebytes,poses,clips,detail vs previous assembler; fixture replay, not live timing')
(checkpoint/'parity.json').write_text(json.dumps(result,indent=2));print(result)
