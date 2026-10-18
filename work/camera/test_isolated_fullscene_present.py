"""Diagnostic full-scene presentation isolation; no live game simulation."""
import ctypes as C,time,struct,json,hashlib,argparse
parser=argparse.ArgumentParser();parser.add_argument("--swap-interval",type=int,choices=(0,1));opt=parser.parse_args()
from pathlib import Path
setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0];exec(compile(setup,'fullscene-fixture','exec'))
g=C.CDLL(str(Path('work/camera/owned-sky-gpu.dll').resolve()));P=C.c_void_p
args=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double]
g.nf_owned_gpu_poll_draw_scene_clips_sky.argtypes=args;g.nf_owned_gpu_present_timed.argtypes=[C.c_uint64,P];g.nf_owned_gpu_present_stages.argtypes=[P];g.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
frame,cm,models,bounds,detail=prepared.sample(.5);raw=bytearray(frame);h=struct.unpack_from('<6I2Q',raw);bg=40+h[2]+h[3];epoch=h[6]
lower=bytes(raw[bg+10560:bg+25696]);upper=lower[1:]+lower[:1];raw[bg+38400+10560:bg+38400+25696]=bytes([1])*15136;frame=bytes(raw)
call=(frame,len(frame),cm,models,bounds,detail['geometry_records'],lower,upper,15136,.375)
out=C.create_string_buffer(3840*2160*3);rows=[]
try:
 assert g.nf_owned_gpu_window(1)==0
 g.nf_owned_gpu_swap_interval.argtypes=[C.c_int,P];swap=(C.c_int*2)();assert g.nf_owned_gpu_swap_interval(-1 if opt.swap_interval is None else opt.swap_interval,swap)==0
 assert g.nf_owned_gpu_poll_draw_scene_clips_sky(*call)==0;assert g.nf_owned_gpu_read(out,len(out))==0;before=hashlib.sha256(out.raw).hexdigest()
 origin=time.perf_counter_ns()
 for index in range(600):
  begin=time.perf_counter_ns();assert g.nf_owned_gpu_poll_draw_scene_clips_sky(*call)==0;draw_end=time.perf_counter_ns();deadline=origin+(index+1)*1000000000//60
  while True:
   remaining=deadline-time.perf_counter_ns()
   if remaining<=0:break
   time.sleep(min(.001,remaining/1e9))
  present_begin=time.perf_counter_ns();total=C.c_uint64();stages=(C.c_uint64*3)();assert g.nf_owned_gpu_present_timed(epoch,C.byref(total))==0;assert g.nf_owned_gpu_present_stages(stages)==0;end=time.perf_counter_ns();assert sum(stages)<=total.value
  rows.append(dict(index=index,begin_ns=begin,draw_end_ns=draw_end,deadline_ns=deadline,present_begin_ns=present_begin,end_ns=end,present_ns=total.value,device_stages_ns=list(stages)))
 assert g.nf_owned_gpu_poll_draw_scene_clips_sky(*call)==0 and g.nf_owned_gpu_read(out,len(out))==0;after=hashlib.sha256(out.raw).hexdigest();assert after==before
finally:
 assert g.nf_owned_gpu_close()==1;prepared.close();history.close()
gaps=[(b['end_ns']-a['end_ns'])/1e6 for a,b in zip(rows,rows[1:])]
report=dict(swap_interval=list(swap),result='PASS_ISOLATION',frames=len(rows),framebuffer_sha256=before,summary=dict(swap_max_ms=max(x['device_stages_ns'][1] for x in rows)/1e6,swap_over_refresh=sum(x['device_stages_ns'][1]>1e9/60 for x in rows),draw_max_ms=max(x['draw_end_ns']-x['begin_ns'] for x in rows)/1e6,max_gap_ms=max(gaps),gaps_over_two_refreshes=sum(x>1000/30 for x in gaps)),rows=rows,scope='Visible fixed full4K world/HUD fixture with fractional synthetic sky; no producer/simulation/preparation worker/audio. CPU completion, no physical scanout or live gameplay proof.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/isolated-fullscene-present-20261006');cp.mkdir(exist_ok=True);(cp/('report-default.json' if opt.swap_interval is None else 'report-swap'+str(opt.swap_interval)+'.json')).write_text(json.dumps(report,indent=2));print(report['summary'])
