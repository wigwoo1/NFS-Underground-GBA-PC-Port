import ctypes as C,struct,json,statistics
from pathlib import Path
import _owned_frame_capture_prepared_profile_candidate as m
raw=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];refresh=struct.unpack_from('<I',raw,4)[0]
Reader=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
@Reader
def reader(e,r,p,n,w):
 w[0]=len(raw)
 if p:C.memmove(p,raw,len(raw))
 return 1
rows=[]
for i in range(12):
 capsule=m.prepare(0x1000000);packet=m.capture(capsule,C.cast(reader,C.c_void_p).value,epoch,refresh);assert packet==raw
 s=m.stats();assert s[6]==len(raw) and 0<=s[4]<=s[3]
 rows.append(dict(moved=bool(s[0]),resize_ms=s[1]*1000/s[2],resident_fraction=s[4]/s[3],read_ms=s[5]*1000/s[2]))
result=dict(result='PASS_PREPARED_SHRINK_RESIDENCY_PARITY',rows=rows,moved=sum(r['moved'] for r in rows),median_resident_fraction=statistics.median(r['resident_fraction'] for r in rows),median_resize_ms=statistics.median(r['resize_ms'] for r in rows),scope='16MiB prepared buffers shrunk to captured fixture size, byte-exact output. Component allocator behavior only; not live game or60fps evidence.')
Path('work/camera/prototype-runs/prepared-shrink-residency-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
