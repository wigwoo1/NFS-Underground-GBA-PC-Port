from pathlib import Path
import ctypes as C,json
from scene_batches import records
from wall_native_prepared import prepared_edge
p=Path('work/camera');events={e['id']:e for e in records(p/'motion-original-source-8750-8781.bin')};snap=json.loads((p/'motion-wall-snapshots.json').read_text());table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for scene in snap['scenes']:
 for wall in scene['walls']:
  actual=prepared_edge(wall,table);expected=events[wall['event']]['blocks'][6][1];checks.append(dict(event=wall['event'],actual_hex=actual.hex(),expected_hex=expected.hex(),exact=actual==expected,differences=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]))
r=dict(result='PASS_NATIVE_WALL_PREPARED_EDGES' if all(v['exact'] for v in checks) else 'WALL_PREPARED_EDGE_DIFFERENCE',checks=checks,scope='Native uncut default52byte wall edge fromworld/source attrs/material/animation. No capturededge usedasnative input; nearclip/extended unsupported andcolumnstate/render pending.')
(p/'motion-wall-prepared-tests.json').write_text(json.dumps(r,indent=2));print(r['result']);print([v for v in checks if not v['exact']][:2])
