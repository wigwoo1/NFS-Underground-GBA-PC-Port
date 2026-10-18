import ctypes as C,struct,json
from pathlib import Path
from owned_exact_prepared_service_candidate import ExactPreparedFrames
raw=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];refresh=struct.unpack_from('<I',raw,4)[0]
variant=bytearray(raw[:40]+b'x'+raw[40:]);struct.pack_into('<I',variant,8,struct.unpack_from('<I',raw,8)[0]+1);variant=bytes(variant);current=raw
Reader=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
@Reader
def reader(e,r,p,n,w):
 w[0]=len(current)
 if p:
  if n<len(current):return 0
  C.memmove(p,current,len(current))
 return 1
service=ExactPreparedFrames()
try:
 for current in (raw,variant,raw):
  assert service.capture(C.cast(reader,C.c_void_p).value,epoch,refresh)==current
  with service.cv:assert service.cv.wait_for(lambda:len(service.ready)==2 or service.error,10)
  assert service.capture(C.cast(reader,C.c_void_p).value,epoch,refresh)==current
finally:shutdown=service.close()
assert shutdown['hits']==3 and shutdown['misses']==3 and shutdown['joined'] and shutdown['pending']==0 and shutdown['peak']==2
print(shutdown)
Path('work/camera/prototype-runs/exact-prepared-component-20261009.json').write_text(json.dumps(dict(result='PASS_EXACT_SIZE_MATCH_FALLBACK',shutdown=shutdown),indent=2))
