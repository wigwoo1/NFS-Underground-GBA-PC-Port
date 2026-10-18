import ctypes as C,json,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-hud-copy-candidate.dll').resolve()));P=C.c_void_p
assert d.nf_d3d_open()==0
d.nf_d3d_clear.argtypes=[P];d.nf_d3d_copy_target.argtypes=[C.c_uint];d.nf_d3d_draw.argtypes=[P,C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,P];d.nf_d3d_read.argtypes=[P,C.c_size_t];d.nf_d3d_stats.argtypes=[P]
f=[];t=threading.Thread(target=lambda:f.append(d.nf_d3d_copy_target(100)));t.start();t.join();assert f==[1]
assert d.nf_d3d_copy_target(0)==1 and d.nf_d3d_copy_target(4096)==1
red=(C.c_float*4)(1,0,0,1);green=(C.c_float*4)(0,1,0,1)
assert d.nf_d3d_clear(red)==0 and d.nf_d3d_copy_target(100)==0 and d.nf_d3d_clear(green)==0
vertices=[]
for x,y,u,v in [(0,0,0,0),(3840,0,1,0),(0,2160,0,1),(3840,0,1,0),(3840,2160,1,1),(0,2160,0,1)]:vertices.extend([x,y,u,v,0,1,1,1,1,1])
a=(C.c_float*len(vertices))(*vertices);config=(C.c_float*8)(0,3840,2160,0,1,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,0,0,3840,2160)
assert d.nf_d3d_draw(a,6,100,0,0,config,rect)==0
out=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(out,len(out))==0;assert out.raw==bytes([255,0,0,255])*(3840*2160)
assert d.nf_d3d_clear(green)==0 and d.nf_d3d_copy_target(100)==0
assert d.nf_d3d_draw(a,6,100,0,0,config,rect)==0 and d.nf_d3d_read(out,len(out))==0;assert out.raw==bytes([0,255,0,255])*(3840*2160)
stats=(C.c_uint64*4)();d.nf_d3d_stats(stats);before=list(stats);assert before[2]==1;assert d.nf_d3d_close()==0;d.nf_d3d_stats(stats);assert stats[2]==stats[3]==0
r=dict(result='PASS_GPU_TARGET_COPY_COMPONENT',pixels_checked_per_snapshot=3840*2160,stable_snapshot_after_target_clear=True,replacement_snapshot=True,foreign_thread_rejected=True,invalid_ids_rejected=True,before=before,after=list(stats),scope='GPU render-target copy and texture sampling only; HUD shader and full-scene/live parity pending.')
(p/'prototype-runs/d3d-hud-copy-component.json').write_text(json.dumps(r,indent=2));print(r)
