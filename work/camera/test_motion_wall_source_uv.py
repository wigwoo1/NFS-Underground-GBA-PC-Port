from pathlib import Path
import ctypes as C,json,struct
from scene_batches import records
p=Path('work/camera');events={e['id']:e for e in records(p/'motion-original-source-8750-8781.bin')};snap=json.loads((p/'motion-wall-snapshots.json').read_text());fn=C.CDLL(str((p/'wall-source-uv.dll').resolve())).nf_wall_source_uv;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p];checks=[]
for scene in snap['scenes']:
 for wall in scene['walls']:
  e=events[wall['event']];source=bytes.fromhex(wall['source_hex']);anim=bytes.fromhex(wall['animation_hex']);shift=struct.unpack_from('<H',bytes.fromhex(wall['material_hex']),36)[0];out=(C.c_uint32*6)();assert fn(source,anim,shift,wall['flags'],out);expected=list(struct.unpack_from('<6I',e['blocks'][6][1],16));checks.append(dict(event=wall['event'],actual=list(out),expected=expected,exact=list(out)==expected))
r=dict(result='PASS_ACTUAL_WALL_RAW_UV' if all(v['exact'] for v in checks) else 'WALL_RAW_UV_DIFFERENCE',checks=checks,scope='Six source/animation UV fields before nearclipping/perspective restoration,35actual uncut walls. Auto-horizontal ordering after sourceUV setup remains separate. No fullcolumn/render proof.')
(p/'motion-wall-source-uv-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks));print([v for v in checks if not v['exact']][:2])
