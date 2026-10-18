"""Join closed original external car builders to exact captured model poses."""
import sys,json,struct
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
from owned_external_model_projection import external_model_matrix
from owned_motion_pairs import records
r=json.loads(Path(sys.argv[1]).read_text());checks=[]
for capture in r['model_scene_captures']:
 rows=[row for row in records(Path(capture['frame']).read_bytes())['records'] if row['kind']==3]
 builders=OwnedModelBuilders(Path(capture['builders']).read_bytes())
 for values in builders.records.values():
  b=values[-1]
  if b.external_enabled and struct.unpack_from('<H',b.source,10)[0]&32:
   matrix=external_model_matrix(b);matches=[row for row in rows if bytes(row['blocks'][2])==matrix]
   if not matches:continue # Retained builder outside current draw coverage is not a visible draw.
   assert len(matches)==1
   checks.append(dict(refresh=capture['refresh'],builder_refresh=b.refresh,source=b.object_address,matrix=b.matrix_address,exact=True))
assert checks,'No external car pose joined'
Path(sys.argv[1]).with_suffix('.closed-external-poses.json').write_text(json.dumps(checks,indent=2))
print('PASS closed external provenance reproduces original captured car pose:',len(checks),'scene joins')
