"""Independent source-clock math and atomic rejection tests; no game execution."""
import argparse,ctypes as C,json,math,os,struct
from fractions import Fraction
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--capture",type=Path,required=True)
p.add_argument("--bridge",type=Path,required=True)
p.add_argument("--runtime",type=Path,required=True)
p.add_argument("--report",type=Path,required=True)
a=p.parse_args();data=json.loads(a.capture.read_text())
rows=data["pose_boundaries"];timing=data["scene_timing"]
with os.add_dll_directory(str(a.runtime)),os.add_dll_directory(str(a.bridge.parent)):
 d=C.CDLL(str(a.bridge))
 d.nf_source_pose_phase.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_uint64),C.c_void_p,C.c_size_t,C.POINTER(C.c_uint64),C.c_double,C.POINTER(C.c_double)]
 d.nf_source_pose_camera.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p]
 d.nf_source_pose_object.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t,C.c_void_p]
 phase_cases=clock_cases=invalid_cases=0;max_error=0
 for row,t in zip(rows,timing):
  c=row["source_clock"];meta=row["meta"]
  assert c[:2]==meta[4:6] and 0<=c[2]<280896
  until=t[11] if t[11]<2**63 else t[11]-2**64
  flip_phase=((t[9]-160)%228)*1232+(1232 if t[10]&2 else 1008)-until
  assert t[4]-c[0]==(t[3]-c[1])*280896+flip_phase-c[2]
  clock_cases+=1
 for old,new in zip(rows,rows[1:]):
  a_raw=bytes.fromhex(old["raw_hex"]);b_raw=bytes.fromhex(new["raw_hex"])
  ca=(C.c_uint64*3)(*old["source_clock"]);cb=(C.c_uint64*3)(*new["source_clock"])
  lo=Fraction(ca[1])+Fraction(ca[2],280896);hi=Fraction(cb[1])+Fraction(cb[2],280896)
  assert hi>lo and (hi-lo)*280896==cb[0]-ca[0]
  for index in range(9):
   fraction=Fraction(index,8);target=float(lo+(hi-lo)*fraction);out=C.c_double(77)
   assert d.nf_source_pose_phase(a_raw,len(a_raw),ca,b_raw,len(b_raw),cb,target,C.byref(out))
   # Target is a double. Compute its mathematically exact interpolation phase
   # independently with rational arithmetic, including target rounding.
   reference=float((Fraction.from_float(target)-lo)/(hi-lo))
   error=abs(out.value-reference);assert error<1e-10
   assert abs(out.value-float(fraction))<1e-9
   max_error=max(max_error,error);phase_cases+=1
 # Reject independent time/identity/size changes atomically on an actual pair.
 old,new=rows[:2];ar=bytes.fromhex(old["raw_hex"]);br=bytes.fromhex(new["raw_hex"])
 ca=(C.c_uint64*3)(*old["source_clock"]);cb=(C.c_uint64*3)(*new["source_clock"])
 lo=ca[1]+ca[2]/280896;hi=cb[1]+cb[2]/280896;target=(lo+hi)/2
 def reject(x,n,c,y,m,e,t):
  global invalid_cases
  out=C.c_double(77);assert not d.nf_source_pose_phase(x,n,c,y,m,e,t,C.byref(out)) and out.value==77
  invalid_cases+=1
 for value in (lo-.01,hi+.01,float("nan"),float("inf")):reject(ar,len(ar),ca,br,len(br),cb,value)
 reject(ar,len(ar)-1,ca,br,len(br),cb,target)
 for index,value in ((0,cb[0]+1),(1,cb[1]+1),(2,280896)):
  bad=(C.c_uint64*3)(*cb);bad[index]=value;reject(ar,len(ar),ca,br,len(br),bad,target)
 for offset,value in ((0,old["meta"][0]+1),(8,old["meta"][1]),(48,new["meta"][6]^4),(56,new["meta"][7]^4),(64,new["meta"][8]^4)):
  bad=bytearray(br);struct.pack_into("<Q",bad,offset,value);reject(ar,len(ar),ca,bytes(bad),len(bad),cb,target)
 reject(br,len(br),cb,ar,len(ar),ca,target)
 # Camera degeneracy and unsupported ordinary objects must preserve output.
 sentinel=C.create_string_buffer(b"M"*56);before=sentinel.raw
 bad=bytearray(ar);bad[128:176]=bytes(48)
 assert not d.nf_source_pose_camera(bytes(bad),len(bad),sentinel) and sentinel.raw==before;invalid_cases+=1
 for slot in range(5):
  at=176+slot*208;flags=struct.unpack_from("<H",ar,at+14)[0]
  if not flags&32:
   address=struct.unpack_from("<I",ar,at)[0]
   assert not d.nf_source_pose_object(ar,len(ar),address,None,0,sentinel) and sentinel.raw==before;invalid_cases+=1
 sums=[sum(r["original_projection_audit"][i] for r in rows) for i in range(4)]
 details=[dict(serial=r["meta"][1],object=hex(r["original_projection_detail"][0]),
       flags=hex(r["original_projection_detail"][2]),read_mask=r["original_projection_detail"][3],
       predicted=r["original_projection_detail"][4:16],actual=r["original_projection_detail"][16:28])
       for r in rows if r["original_projection_detail"]]
 result=dict(source_clock_result="PASS",source_to_flip_exact_cycle_checks=clock_cases,
  fractional_phase_cases=phase_cases,max_phase_rational_error=max_error,atomic_invalid_cases=invalid_cases,
  orientation_result="UNRESOLVED_PLAYER_TRANSFORM",original_matrix_audit=dict(entries=sums[0],angle_entries=sums[1],external_entries=sums[2],mismatches=sums[3]),
  first_mismatch=details[0] if details else None,
  current_packet_orientation_matches=sum(r["source_pose_orientations_verified"] for r in rows),
  supported_external_packet_models=sum(r["source_pose_supported"] for r in rows),
  scope="Exact source clock/phase and rejection components only; player pose reconstruction remains unsupported. No displayed interpolation change or 60fps gameplay claim.")
 a.report.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
