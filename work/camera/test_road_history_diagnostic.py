import ctypes as C,json
from pathlib import Path
from owned_road_history_diagnostic import snapshot,restore
lib=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));lib.nf_road_scratch_destroy.argtypes=[C.c_void_p];lib.nf_road_scratch_clone.argtypes=[C.c_void_p];lib.nf_road_scratch_clone.restype=C.c_void_p
payload=dict(abi='RoadScratch-u32-address512-f64-depth512-v1',rows=[(0x2000000+i*24,i*.125) for i in range(512)])
a=restore(lib,json.loads(json.dumps(payload)));b=lib.nf_road_scratch_clone(a)
try:
 assert snapshot(a)==snapshot(b)
 assert snapshot(a)['rows']==payload['rows']
 for bad in (dict(payload,abi='bad'),dict(payload,rows=[(1,float('nan'))]),dict(payload,rows=[(1,2),(1,3)])):
  try:restore(lib,bad);raise AssertionError('invalid accepted')
  except ValueError:pass
 print('PASS:512-slot JSON restore/native clone equality,invalid ABI/nonfinite/duplicate rejection')
finally:lib.nf_road_scratch_destroy(a);lib.nf_road_scratch_destroy(b)
