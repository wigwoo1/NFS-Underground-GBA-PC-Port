import ctypes as C,json,struct,time,statistics
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'exact-equal-sse2-candidate.dll').resolve()));P=C.c_void_p
for f in (d.equal_sse2,d.equal_original):f.argtypes=[P,P,C.c_size_t];f.restype=C.c_int
k=C.WinDLL('kernel32',use_last_error=True);k.VirtualAlloc.argtypes=[P,C.c_size_t,C.c_uint,C.c_uint];k.VirtualAlloc.restype=P;k.VirtualProtect.argtypes=[P,C.c_size_t,C.c_uint,P];k.VirtualFree.argtypes=[P,C.c_size_t,C.c_uint]
alloc=[];checks=0
try:
 for _ in range(2):
  a=k.VirtualAlloc(None,8192,0x3000,4);assert a;alloc.append(a);old=C.c_uint();assert k.VirtualProtect(a+4096,4096,1,C.byref(old))
 for n in list(range(66))+[127,128,129,255,256,257,4095,4096]:
  a,b=[v+4096-n for v in alloc];data=bytes((i*37)%256 for i in range(n));C.memmove(a,data,n);C.memmove(b,data,n);assert d.equal_sse2(a,b,n)==d.equal_original(a,b,n)==1;checks+=1
  for position in set([0,n//2,n-1]) if n else []:
   C.c_uint8.from_address(b+position).value^=1;assert d.equal_sse2(a,b,n)==d.equal_original(a,b,n)==0;checks+=1;C.c_uint8.from_address(b+position).value^=1
finally:
 for a in alloc:assert k.VirtualFree(a,0,0x8000)
report=json.loads((p/'prototype-runs/owned-native-1791434872973979000.json').read_text());folder=Path(report['live_preparation_profiles'][0]['capture']);hud=[]
for name in ('older.frame.bin','newer.frame.bin'):
 f=(folder/name).read_bytes();gn,hn=struct.unpack_from('<II',f,8);hud.append(f[40+gn:40+gn+hn]);assert len(hud[-1])==5591040
owners=[C.create_string_buffer(hud[0]),C.create_string_buffer(hud[0]),C.create_string_buffer(hud[1])]
for a in owners:
 for b in owners:assert d.equal_sse2(a,b,5591040)==d.equal_original(a,b,5591040);checks+=1
trials=[]
for i in range(8):
 row={}
 for name in (('original','sse2') if i%2==0 else ('sse2','original')):
  fn=d.equal_original if name=='original' else d.equal_sse2;cost=[]
  for _ in range(20):
   begin=time.perf_counter_ns();assert fn(owners[0],owners[1],5591040)==1;cost.append(time.perf_counter_ns()-begin)
  row[name]=statistics.median(cost)/1e6
 trials.append(row)
out=dict(result='PASS_EXACT_SSE2_GUARD_CAPTURED_PARITY',checks=checks,trials=trials,median_trial_ms={k:statistics.median(x[k] for x in trials) for k in ('original','sse2')},scope='Guarded tails, unaligned starts, zero length, first/middle/last mismatches and actual capturedHUD exact comparison. Eight alternating standalone pairs on equal5591040byteHUD; no fullrenderer/game cadence proof.')
(p/'prototype-runs/exact-equal-sse2-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],out['checks'],out['median_trial_ms'])
