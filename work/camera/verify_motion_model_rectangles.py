from pathlib import Path
import ctypes as C,json,struct
from scene_batches import records,batches
p=Path('work/camera');old=list(records(p/'motion-original-span-world.bin'));new=list(records(p/'motion-original-model-rect-world.bin'));assert len(old)==len(new)
for a,b in zip(old,new):
 assert all(a[k]==b[k] for k in ('pc','frame','id','regs'))
 assert a['blocks']=={k:v for k,v in b['blocks'].items() if k!=90}
models={m['event']:m for m in json.loads((p/'native-motion-model-faces.json').read_text())['models']};snap={m['event']:m for s in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in s['models']};f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_polygon_classify;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];checks=[]
for e in new:
 if e['id'] not in models:continue
 assert len(e['blocks'][90][1])==16
 rect=list(struct.unpack('<4i',e['blocks'][90][1]));m=models[e['id']];points=struct.pack('<'+'h'*len(m['points'])*2,*[v for xy in m['points'] for v in xy]);flags=[]
 for face in snap[e['id']]['faces']:
  idx=(C.c_uint16*len(face['vertices']))(*face['vertices']);out=C.c_int();assert f(points,len(m['points']),idx,len(idx),(C.c_int32*4)(*rect),C.byref(out));flags.append(out.value)
 checks.append(dict(event=e['id'],rectangle_address=e['blocks'][90][0],rectangle=rect,face_flags=flags))
assert len(checks)==7
r=dict(result='CAPTURED_MODEL_RECTANGLES_UNCHANGED_ORIGINAL',existing_events_exact=len(old),model_draws=len(checks),checks=checks,scope='New read-only rectangle capture preserves all previous event/register/block data and final RAM. Native classifier evaluated actual captured bounds; exact classifier ARM parity established separately. Full clipping/UV/raster not verified.')
(p/'motion-model-rectangle-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('checks','scope')});print([c['rectangle'] for c in checks])
