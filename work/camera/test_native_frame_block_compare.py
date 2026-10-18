import ctypes as C,time,statistics,json
from pathlib import Path
f=Path('work/camera/prototype-runs/child-scene-1791637661169682300');a=(f/'older.frame.bin').read_bytes();b=(f/'newer.frame.bin').read_bytes();d=C.CDLL(str(Path('work/camera/native-frame-block-compare-candidate.dll').resolve()));fn=d.nf_frame_block_compare;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_size_t,C.c_void_p,C.c_size_t]
rows=[]
for block in (16384,65536,262144):
 count=(len(a)+block-1)//block;flags=(C.c_uint8*count)();times=[];complete=[]
 expected=[int(a[i:i+block]!=b[i:i+block]) for i in range(0,len(a),block)]
 for repeat in range(12):
  begin=time.perf_counter_ns();assert fn(a,b,len(a),block,flags,count)==count;scanned=time.perf_counter_ns();assert list(flags)==expected
  patches=[(i*block,b[i*block:(i+1)*block]) for i in range(count) if flags[i]];rebuilt=bytearray(a)
  for at,body in patches:rebuilt[at:at+len(body)]=body
  rebuilt=bytes(rebuilt);end=time.perf_counter_ns();assert rebuilt==b;times.append((scanned-begin)/1e6);complete.append((end-begin)/1e6)
 rows.append(dict(block=block,median_scan_ms=statistics.median(times),median_scan_patch_rebuild_ms=statistics.median(complete),patch_bytes=sum(len(v) for _,v in patches)))
flags=(C.c_uint8*4)(9,9,9,9)
for n,block,capacity in ((0,1024,4),(16777217,1024,4),(4,0,4),(4,1024,0)):
 assert fn(a,b,n,block,flags,capacity)==37 and list(flags)==[9]*4
small_a=b'abcd';small_b=b'abce';assert fn(small_a,small_b,4,1024,flags,4)==1 and flags[0]==1
assert fn(small_a,small_a,4,1024,flags,4)==1 and flags[0]==0
result=dict(result='PASS_NATIVE_BLOCK_COMPARE_COMPONENT',rows=rows,invalid_extents_preserve_output=True,scope='One actual equal-size captured pair plus bounds/identical/lastpartial checks. Complete timings include private reconstruction, not wire/capability/live/GPU qualification.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/native-block-compare-component.json').write_text(json.dumps(result,indent=2));print(result)
