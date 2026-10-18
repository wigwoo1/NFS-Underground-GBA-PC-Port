import ctypes as C,json
from pathlib import Path
Info=C.CFUNCTYPE(C.c_int,C.POINTER(C.c_uint));Copy=C.CFUNCTYPE(C.c_int,C.c_uint,C.c_void_p,C.c_size_t);Count=C.CFUNCTYPE(C.c_uint);Records=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_size_t)
checks=[]
for name in ['owned-d3d-call-profile-candidate.dll','owned-d3d-hud-phase-candidate.dll']:
 d=C.CDLL(str(Path('work/camera',name).resolve()));d.nf_d3d_source_hud_batch.argtypes=[C.c_void_p]*4
 assert d.nf_d3d_source_hud_batch(None,None,None,None)==1
 assert d.nf_d3d_open()==0
 try:
  called=[]
  @Info
  def info(p):p[0]=0;p[1]=0;called.append('info');return 0
  @Copy
  def copy(*args):called.append('copy');return 1
  @Count
  def count():called.append('count');return 0
  @Records
  def records(*args):called.append('records');return 1
  assert d.nf_d3d_source_hud_batch(info,copy,count,records)==0 and called==['info']
  if 'hud-phase' in name:
   ticks=(C.c_uint64*12)();d.nf_d3d_hud_phase_ticks.argtypes=[C.c_void_p,C.c_size_t]
   assert d.nf_d3d_hud_phase_ticks(ticks,C.sizeof(ticks))==0
   assert ticks[0]>0 and ticks[1]>0 and all(x==0 for x in ticks[2:])
   assert d.nf_d3d_hud_phase_ticks(ticks,1)==1
  checks.append(name)
 finally:assert d.nf_d3d_close()==0
out=dict(result='PASS_NATIVE_HUD_DISABLED_AND_ARGUMENT_GUARDS',backends=checks,scope='Real native device open/close and disabled-HUD/invalid-pointer parity; enabled HUD pixels and live timing unverified.')
Path('work/camera/prototype-runs/native-hud-phase-guards-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
