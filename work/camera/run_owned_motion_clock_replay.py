"""Scheduled source-pose diagnostic replay; not live gameplay verification."""
from pathlib import Path
import ctypes as C,time,json
from owned_motion_clock import scene_samples
from sample_owned_motion import sample
p=Path('work/camera');refs=[8758,8762,8766,8769,8773,8776,8780];frames=[(p/'motion-actual-scanline-assets'/f'{r}-native-complete-frame.bin').read_bytes() for r in refs];d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_poses.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_present.argtypes=[C.c_uint64];results=[]
try:
 assert d.nf_owned_gpu_window(0)==0;assert d.nf_owned_gpu_draw(frames[0],len(frames[0]))==0
 origin=time.perf_counter_ns()
 for j,(older,newer) in enumerate(zip(refs,refs[1:])):
  for slot in scene_samples(origin,refs[0],older,newer):
   begin=time.perf_counter_ns();frame,cm,models=sample(frames[j],frames[j+1],slot['alpha'])
   if cm is None:assert d.nf_owned_gpu_draw(frame,len(frame))==0
   else:assert d.nf_owned_gpu_draw_poses(frame,len(frame),cm,models,len(models)//12)==0
   end=time.perf_counter_ns()
   while True:
    left=slot['deadline_ns']-time.perf_counter_ns()
    if left<=0:break
    time.sleep(min(left/1e9,.001))
   presented=time.perf_counter_ns();assert d.nf_owned_gpu_present(2)==0;finished=time.perf_counter_ns()
   results.append(dict(**slot,source_older=older,source_newer=newer,prepare_draw_cpu_ns=end-begin,present_begin_ns=presented,present_end_ns=finished))
finally:assert d.nf_owned_gpu_close()
assert all(b['index']==a['index']+1 for a,b in zip(results,results[1:]))
r=dict(result='PASS_SCHEDULED_RAW_POSE_DIAGNOSTIC',presentations=len(results),max_present_lateness_ns=max(x['present_begin_ns']-x['deadline_ns'] for x in results),max_prepare_draw_cpu_ns=max(x['prepare_draw_cpu_ns'] for x in results),samples=results,scope='Retained immutable sources, hidden window22consecutive60Hzgridcommits. Does not include live game producer, verify scanout/GPU completion, intermediate clipping fidelity or smooth60fps gameplay.')
(p/'owned-motion-clock-replay-tests.json').write_text(json.dumps(r,indent=2));print({k:r[k] for k in ('result','presentations','max_present_lateness_ns','max_prepare_draw_cpu_ns')})
