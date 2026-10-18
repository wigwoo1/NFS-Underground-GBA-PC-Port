import ctypes as C,struct,hashlib,json
from pathlib import Path
import _owned_frame_capture_prepared_candidate as native
from owned_prepared_frame_service_candidate import PreparedFrames
raw=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];refresh=struct.unpack_from('<I',raw,4)[0]
Reader=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
mode='valid'
@Reader
def reader(e,r,p,n,w):
 w[0]=len(raw)
 if not p:return 1
 if mode=='partial':C.memmove(p,raw,40);return 0
 C.memmove(p,raw,len(raw))
 if mode=='short':w[0]-=1
 if mode=='identity':C.c_uint64.from_address(p+24).value+=1
 return 1
address=C.cast(reader,C.c_void_p).value
capsule=native.prepare(len(raw));packet=native.capture(capsule,address,epoch,refresh);assert packet==raw
try:native.capture(capsule,address,epoch,refresh)
except ValueError:pass
else:raise AssertionError('Double consumption accepted')
service=PreparedFrames();published=[]
try:
 for mode in ('valid','partial','short','identity','valid'):
  if mode=='valid':published.append(service.capture(address,epoch,refresh));assert published[-1]==raw
  else:
   try:service.capture(address,epoch,refresh)
   except ValueError:pass
   else:raise AssertionError('Partial frame published')
 assert all(p==raw for p in published)
finally:shutdown=service.close()
assert shutdown['joined'] and shutdown['pending']==0 and shutdown['peak']<=2
try:service.capture(address,epoch,refresh)
except RuntimeError:pass
else:raise AssertionError('Closed service accepted capture')
mode='valid';small=native.prepare(40)
try:native.capture(small,address,epoch,refresh)
except ValueError:pass
else:raise AssertionError('Capacity accepted')
result=dict(result='PASS_PREPARED_PRIVATE_STORAGE_COMPONENT',shutdown=shutdown,scope='Captured frame fixture parity, single consumption, partial/short/identity failure discard, recovery, capacity guard and close. Not live renderer integration or timing proof. Shrink may move allocation; residency must be measured.')
Path('work/camera/prototype-runs/prepared-storage-component-20261009.json').write_text(json.dumps(result,indent=2));print(result)
