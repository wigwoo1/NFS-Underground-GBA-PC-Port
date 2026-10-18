"""Owned raw capture adapter; whole source decoding and drawing plan execute in C."""
import ctypes as C
from scene_batches import records,batches
import json

def model_commands(p):
 d=C.CDLL(str((p/'native_model.dll').resolve()));f=d.nfs_model_source_rows
 f.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());commands=[]
 selected={m['event'] for scene in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in scene['models']}
 for event in records(p/'motion-original-model-rect-world.bin'):
  if event['id'] not in selected:continue
  b=event['blocks'];raw=[b[tag][1] for tag in [51,52,53,56,54,60,58,59,65,90]];buffers=[C.create_string_buffer(x) for x in raw];ptrs=(C.c_void_p*10)(*[C.addressof(x) for x in buffers]);sizes=(C.c_uint*10)(*[len(x) for x in raw]);out=(C.c_uint32*(65536*7))();count=C.c_uint()
  assert f(ptrs,sizes,table,out,65536,C.byref(count)),('unsupported owned model',event['id'])
  context=raw[0];shift=int.from_bytes(context[56:58],'little');texture=int.from_bytes(context[52:56],'little')
  commands.extend(dict(event=event['id'],polygon=out[i*7],params=list(out[i*7+1:(i+1)*7]),texture=texture,shift=shift) for i in range(count.value))
 return commands
