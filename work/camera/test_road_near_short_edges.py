from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-near-continuous.dll').resolve())).nf_road_near_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700])
def sample(distance,ratio=.3):
 a=[-20,100,64-ratio*distance,200,300];b=[80,100,64+(1-ratio)*distance,400,900];out=(C.c_double*5)();assert fn((C.c_double*5)(*a),(C.c_double*5)(*b),64,table,out);assert all(math.isfinite(v) for v in out);return list(out)
checks=0;seams=[]
for ratio in (.1,.3,.5,.9):
 for d in (1e-7,1e-5,.01,.1,.5,.999999,1,1.000001,2):sample(d,ratio);checks+=1
 l=sample(1-1e-8,ratio);r=sample(1+1e-8,ratio);gap=max(abs(x-y) for x,y in zip(l,r));assert gap<1e-4;seams.append(gap)
 out=sample(1e-7,ratio);expected=[-20+100*ratio,100,64,200+200*ratio,300+600*ratio];assert max(abs(x-y) for x,y in zip(out,expected))<1e-3
report=dict(result='PASS',finite_short_edge_checks=checks,distance_one_seam_gaps=seams,degenerate_ratio_limit_checks=4,scope='Synthetic bounded edges only; no GPU/fullscene motion proof.')
(p/'road-near-short-edge-tests.json').write_text(json.dumps(report,indent=2));print(report)
