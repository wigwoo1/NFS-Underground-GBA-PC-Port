"""Instrumentation records survive close and never overrun caller capacity."""
import ctypes as C,json,runpy,sys
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-cpu-profile-20261008')
sys.argv=['test','work/camera/prototype-runs/owned-native-1791430642217389200.json',str(cp/'fullscene-parity.json')]
ns=runpy.run_path('work/camera/test_hud_cpu_profile_4k.py');d=ns['gpu']
d.nf_hud_cpu_profile_count.restype=C.c_uint;d.nf_hud_cpu_profile_read.argtypes=[C.c_void_p,C.c_uint]
n=d.nf_hud_cpu_profile_count();assert n==4,n
out=(C.c_uint64*(n*11))(*([123]*(n*11)));assert not d.nf_hud_cpu_profile_read(out,n-1) and list(out)==[123]*(n*11)
assert not d.nf_hud_cpu_profile_read(None,n);assert d.nf_hud_cpu_profile_read(out,n)
rows=[list(out[i*11:(i+1)*11]) for i in range(n)];assert d.nf_hud_cpu_profile_dropped()==0
assert sum(x[2] for x in rows)==3 and all(x[10]==1 for x in rows)
assert all(x[9]==(0 if x[2] else 160) for x in rows)
assert all(x[k]!=(2**64-1) for x in rows for k in (4,5,6,7,8))
(cp/'records-component.json').write_text(json.dumps(dict(result='PASS',records=rows,capacity_rejection_atomic=True,retained_after_close=True,scope='Four captured4Kcallbacks; valid Windows timing counters, 1miss/3hits, exact buildcounts. No calibration of cycles to CPU nanoseconds or live pacing claim.'),indent=2))
print('PASS retained HUD timing records',n)
