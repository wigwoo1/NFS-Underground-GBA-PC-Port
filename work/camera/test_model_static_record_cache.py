import json
from pathlib import Path
from owned_sample_signature import signature
import owned_sampled_world_frame as world
import owned_prepared_world_motion as prepared_module
setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0];exec(compile(setup,'complete-fixture','exec'))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-static-record-cache-20261006');old={};exec(compile((cp/'assembler.before.py').read_text(),'reference-assembler','exec'),old)
candidate=world.assemble_world
# PreparedWorldMotion imports this function at sample time.
checks=[]
try:
 for i in range(101):
  alpha=i/100
  prepared_module.assemble_world=old['assemble_world'];reference=signature(prepared.sample(alpha))
  prepared_module.assemble_world=candidate;actual=signature(prepared.sample(alpha))
  assert reference==actual,alpha
  checks.append(dict(alpha=alpha,signature=actual))
 entries=len(getattr(prepared.pair,'_ordinary_encoded_models',{}));assert entries>0
finally:prepared_module.assemble_world=candidate;prepared.close();history.close()
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',poses=101,cache_entries=entries,checks=checks,scope='Complete captured frame/camera/model/bounds/detail parity; not performance or live60fps proof'),indent=2));print('PASS101 complete poses, ordinary model cache entries',entries)
