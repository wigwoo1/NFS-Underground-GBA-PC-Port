from pathlib import Path
import ctypes as C,json,struct,math
p=Path('work/camera');rows=json.loads((p/'motion-road-source-endpoints.json').read_text())['checks'];d=C.CDLL(str((p/'road-source-between.dll').resolve()));fn=d.nf_road_source_ring_between;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];camera=d.nf_road_camera_between;camera.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_double,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[];endpoint_vertices=0;camera_limits=0
for cmd in (3,4,7):
 poses=[r for r in rows if r['command']==cmd]
 for a,b in zip(poses,poses[1:]):
  count=len(a['world']);world=(C.c_double*(count*3))(*(v for r in a['world'] for v in r));raw=struct.pack('<6I66i',*a['attributes_header'],*(v for pair in a['attributes'] for v in pair),*([0]*(64-count*2)));ma=bytes.fromhex(a['matrix_hex']);mb=bytes.fromhex(b['matrix_hex']);samples=[];topologies=set()
  for phase in (0.,.25,.5,.75,1.):
   out=(C.c_double*320)();n=C.c_uint();assert fn(world,count,raw,ma,mb,phase,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n));ring=[list(out[i*5:i*5+5]) for i in range(n.value)];assert all(math.isfinite(v) for r in ring for v in r)
   if phase in (0.,1.):expected=a['expected'] if phase==0 else b['expected'];assert ring==expected;endpoint_vertices+=len(ring)
   samples.append(dict(phase=phase,ring=ring));topologies.add(n.value)
  gap=0.
  for point in a['world']:
   limits=[]
   for phase in (.5-1e-8,.5+1e-8):
    out=(C.c_double*3)();assert camera((C.c_double*3)(*point),ma,mb,phase,out);limits.append(list(out));camera_limits+=1
   gap=max(gap,max(abs(u-v) for u,v in zip(*limits)))
  assert gap<.001,gap
  checks.append(dict(command=cmd,begin_a=a['begin'],begin_b=b['begin'],refresh_delta=b['begin']-a['begin'],maximum_mid_camera_gap=gap,emitted_counts=sorted(topologies),samples=samples))
report=dict(result='PASS_SOURCE_POSE_COMPONENT',exact_endpoint_vertices=endpoint_vertices,camera_limit_evaluations=camera_limits,checks=checks,scope='18actualgame scene camera intervals: planar shortest yaw rotation with per-world-point Q14 arithmetic residuals and sourceorder near/project emission.36exact endpoint streams;90source phase samples. No continuous topology/visibility/road texture/fullscene/GPU/live60fps proof.')
(p/'road-source-between-tests.json').write_text(json.dumps(report,indent=2));print(report['result'],endpoint_vertices,camera_limits,len(checks))
