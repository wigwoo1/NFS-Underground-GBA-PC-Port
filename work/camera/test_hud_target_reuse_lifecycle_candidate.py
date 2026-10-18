import ctypes as C,json
from pathlib import Path
d=C.CDLL(str(Path('work/camera/owned-d3d-hud-target-reuse-candidate.dll').resolve()));d.nf_d3d_hud_target_stats.argtypes=[C.c_void_p]
t=(C.c_uint64*2)();assert d.nf_d3d_copy_target(1004)==1
for epoch in range(2):
 assert d.nf_d3d_open()==0
 try:
  assert d.nf_d3d_copy_target(0)==1 and d.nf_d3d_copy_target(4096)==1
  assert d.nf_d3d_hud_target_stats(t)==0;a,b=t
  for i in range(100):assert d.nf_d3d_copy_target(1004)==0
  assert d.nf_d3d_hud_target_stats(t)==0 and list(t)==[a+1,b+99]
 finally:assert d.nf_d3d_close()==0
 assert d.nf_d3d_hud_target_stats(t)==1
out=dict(result='PASS_HUD_TARGET_NATIVE_REUSE_LIFECYCLE',device_epochs=2,snapshots=200,creates=2,reuses=198,scope='Real native create/reuse/reopen/invalid-ID guards; enabled 4K pixel parity checked separately, not live cadence proof.')
Path('work/camera/prototype-runs/hud-target-reuse-lifecycle-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
