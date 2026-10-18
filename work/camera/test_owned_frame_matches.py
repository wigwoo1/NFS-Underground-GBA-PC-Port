"""Bounded exact native comparison without replacing native queue ownership."""
import ctypes as C,json,hashlib
from pathlib import Path
d=C.CDLL(str(Path('work/camera/owned-frame-handoff.dll').resolve()));P=C.c_void_p;Z=C.c_size_t
fn=C.PYFUNCTYPE(C.c_int,P,Z,P,Z)(C.cast(d.nf_owned_frame_matches,P).value)
checks=[]
for size in (40,5591080,16777216):
 owned=bytes((i*19)%256 for i in range(size));native=C.create_string_buffer(owned);sha=hashlib.sha256(owned).hexdigest()
 assert fn(native,size,owned,size)
 for index in (0,size//2,size-1):
  native[index]=bytes([owned[index]^1]);assert not fn(native,size,owned,size);native[index]=bytes([owned[index]])
 assert not fn(native,size,owned,size-1) and not fn(None,size,owned,size) and not fn(native,size,None,size)
 del native;assert hashlib.sha256(owned).hexdigest()==sha;checks.append(size)
assert not fn(b'x'*40,39,b'x'*40,39) and not fn(b'x'*40,16777217,b'x'*40,16777217)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-reuse-consumer-frame-20261006');(cp/'matches-tests.json').write_text(json.dumps({'result':'PASS','sizes':checks,'scope':'Exact equality/mismatchfirstmiddlelast/bounds/null/immutable lifetime; independent retained bytes, no GPU timing proof'},indent=2));print('PASS bounded exact frame compare',checks)
