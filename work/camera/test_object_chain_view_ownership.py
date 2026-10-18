import json
from pathlib import Path
from types import SimpleNamespace
from owned_ordinary_model_visits import owned_object_chains as reference
from owned_object_chain_views_candidate import owned_object_chains as candidate
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/exact-pair-10331-20261007/scene-inputs');count=0
for name in ['older','newer']:
 closed=SimpleNamespace(objects=(folder/(name+'.objects.bin')).read_bytes());a=reference(closed);b=candidate(closed);assert a==b;assert candidate(closed) is b
 for rows in b.values():
  for index,source in rows:assert source.readonly and source.obj is closed.objects;count+=1
 retained=b
 for i in range(6):candidate(SimpleNamespace(objects=closed.objects))
 assert retained==a
Path('work/camera/object-chain-view-ownership.json').write_text(json.dumps(dict(result='PASS',objects=count,scope='Two captured chains equal byte-copy reference; readonly views retain exact original immutable payload through cache eviction. Not performance or live timing proof.'),indent=2));print('PASS readonly retained ownership',count)
