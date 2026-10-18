import ctypes as C,json,time,statistics
from pathlib import Path
p=Path('work/camera');runs=[]
blocks=[C.create_string_buffer(bytes([i])*4096) for i in range(12)];ptrs=(C.c_void_p*12)(*[C.addressof(b) for b in blocks]);sizes=(C.c_uint*12)(*[4096]*12)
for name in ['native-geometry-reuse-reference.dll','native-geometry-reuse-candidate.dll']:
 d=C.CDLL(str((p/name).resolve()));d.nf_geometry_sources_append.argtypes=[C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint];d.nf_geometry_sources_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p]
 snapshots=[];times=[]
 try:
  for refresh in range(1,161):
   begin=time.perf_counter_ns()
   for kind in (1,2,3):assert d.nf_geometry_sources_append(kind,refresh,ptrs,sizes,12)
   assert d.nf_geometry_sources_close(refresh);times.append((time.perf_counter_ns()-begin)/1e6)
   n=C.c_size_t();assert d.nf_geometry_sources_read(refresh,None,0,C.byref(n));out=C.create_string_buffer(n.value);assert d.nf_geometry_sources_read(refresh,out,len(out),C.byref(n));snapshots.append(out.raw)
   sentinel=C.create_string_buffer(b'unchanged');assert not d.nf_geometry_sources_read(refresh,sentinel,9,C.byref(n));assert sentinel.value==b'unchanged'
   if refresh>16:assert not d.nf_geometry_sources_read(refresh-16,None,0,C.byref(n))
   if refresh>1:
    prev=C.c_size_t();assert d.nf_geometry_sources_read(refresh-1,None,0,C.byref(prev));old=C.create_string_buffer(prev.value);assert d.nf_geometry_sources_read(refresh-1,old,len(old),C.byref(prev));assert old.raw==snapshots[-2]
  assert not d.nf_geometry_sources_append(0,161,ptrs,sizes,12);assert not d.nf_geometry_sources_close(161);n=C.c_size_t();assert not d.nf_geometry_sources_read(161,None,0,C.byref(n))
 finally:d.nf_geometry_sources_reset()
 assert not d.nf_geometry_sources_read(160,None,0,C.byref(n))
 runs.append(dict(name=name,snapshots=snapshots,median_ms=statistics.median(times[32:])))
assert runs[0]['snapshots']==runs[1]['snapshots']
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/geometry-reuse-20261008');cp.mkdir(exist_ok=True)
out=dict(result='PASS',publications=160,retained_previous_exact=True,stale_and_undersized_rejected=True,invalid_publication_rejected=True,reset_rejected=True,timing=[dict(name=x['name'],median_ms=x['median_ms']) for x in runs],scope='Standalone native geometry component, synthetic12-block sources. Not complete game capture, 4K rendering or live pacing proof.')
(cp/'component.json').write_text(json.dumps(out,indent=2));print(out)
