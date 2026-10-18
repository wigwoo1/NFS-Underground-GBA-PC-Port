import json
from pathlib import Path
from owned_sampled_road_clip import camera_buffer_type
for amount in range(1,97):camera_buffer_type(amount)
assert camera_buffer_type.cache_info().currsize==64
kind=camera_buffer_type(18);assert camera_buffer_type(18) is kind
a,b=kind(),kind();a[0]=123;assert b[0]==0
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-position-types-audit-20261007')
(cp/'ownership.json').write_text(json.dumps(dict(result='PASS',distinct_sizes=96,retained_classes=64,private_instances=True,scope='Array type cache bound and independent instances; complete scene parity recorded separately'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print('PASS road type cache bound and private buffers')