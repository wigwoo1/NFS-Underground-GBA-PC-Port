import argparse
options=argparse.ArgumentParser();options.add_argument("--disable-capture",action="store_true");mode=options.parse_args()
import ctypes as C,json,struct,hashlib
import numpy as np
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-continuous-phase-20261011');cp.mkdir(exist_ok=True)
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
for name in ('NF_GPU_BACKGROUND_ONLY','NF_GPU_EXPECT_EPOCH','NF_GPU_WALLS_ONLY'):assert crt._putenv((name+'=').encode())==0
d=C.CDLL(str((p/'owned-sky-gpu.dll').resolve()));api=d.nf_owned_gpu_draw_scene_clips_sky;api.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];checks=[]

item=items[0]
folder=Path(item['folder']);frame=(folder/'frame.bin').read_bytes();h=struct.unpack_from('<6I2Q',frame)
older=SkyBoundary.decode((folder/'older-sky.bin').read_bytes());newer=SkyBoundary.decode((folder/'newer-sky.bin').read_bytes());assert h[6]==older.epoch==newer.epoch and older.refresh<=h[1] and older.refresh<newer.refresh
origin=older.asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);samples=asset.sample(older,newer,item['alpha']);assert samples.lower==(folder/'lower.bin').read_bytes() and samples.upper==(folder/'upper.bin').read_bytes() and samples.weight==item['weight']
arrays={}
for name in ('camera','models','bounds'):
 raw=(folder/(name+'.bin')).read_bytes();assert len(raw)%8==0;arrays[name]=(C.c_double*(len(raw)//8)).from_buffer_copy(raw)
count=len(arrays['bounds'])//4;assert len(arrays['camera'])==12 and len(arrays['models'])==count*12
stats=d.nf_owned_gpu_sky_hud_cache_stats;stats.argtypes=[C.c_void_p]
def counters():
 out=(C.c_uint64*2)();assert stats(out)==0;return list(out)
def draw(value):
 assert api(value,len(value),arrays['camera'],arrays['models'],arrays['bounds'],count,samples.lower,samples.upper,15136,samples.weight)==0
 out=C.create_string_buffer(3840*2160*3);assert d.nf_owned_gpu_read(out,len(out))==0;return out.raw
import time,statistics
api_timed=d.nf_owned_gpu_draw_scene_clips_sky_timed;api_timed.argtypes=api.argtypes+[C.c_void_p]
d.nf_owned_gpu_sky_draw_stages.argtypes=[C.c_void_p];d.nf_owned_gpu_sky_hud_stages.argtypes=[C.c_void_p]
d.nf_owned_gpu_present_timed.argtypes=[C.c_uint64,C.c_void_p]
d.nf_owned_gpu_present_stages.argtypes=[C.c_void_p]
import threading
capture_setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace('visibility-probe-wide.dll','sky-caller-probe.dll')
capture_namespace={};exec(compile(capture_setup,'capture-producer-setup','exec'),capture_namespace);producer=capture_namespace['d']
rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');assert producer.nf_init(str(rom_path).encode(),b'') and producer.nf_state(str(Path('work/race.state').resolve()).encode(),0)
if not mode.disable_capture:
 assert crt._putenv(b'NF_CAPTURE_INDEXED_COPY=1')==0
 assert producer.nf_native_scene_sink(capture_namespace['text_scene_sink'],None)
 rom_owned=rom_path.read_bytes();assert producer.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024)
 assert producer.nf_world_trace(b'') and producer.nf_layer_queue_enable(1) and producer.nf_owned_graph_live_enable(1)
 assert producer.nf_bitmap_text_enable(1)
 model_table=capture_namespace['model_plan_table'];assert producer.nf_native_model_plan_trace(b'',model_table,len(model_table))
original_timer=C.CDLL(str(Path('work/camera/owned-original-update-timer.dll').resolve()));original_timer.nf_original_update_timed.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
stop_producer=threading.Event();producer_rows=[];producer_errors=[]
def run_producer():
 try:
  origin=time.perf_counter_ns();period=280896*1e9/16777216;index=0
  while not stop_producer.is_set():
   deadline=origin+int(index*period);delay=(deadline-time.perf_counter_ns())/1e9
   if delay>0 and stop_producer.wait(delay):break
   begin=time.perf_counter_ns();native=(C.c_uint64*2)();assert original_timer.nf_original_update_timed(C.cast(producer.nf_frame,C.c_void_p),1,native);end=time.perf_counter_ns();producer_rows.append(dict(index=index,begin_ns=begin,end_ns=end,elapsed_ns=end-begin,native_elapsed_ns=int(native[0]),native_thread_cpu_ns=int(native[1]) if native[1]!=2**64-1 else None));index+=1
 except BaseException as error:producer_errors.append(str(error))
producer_thread=threading.Thread(target=run_producer)
records=[]
try:
 assert d.nf_owned_gpu_window(1)==0
 reference=draw(frame)
 producer_thread.start()
 origin=time.perf_counter_ns()
 for i in range(120):
  assert d.nf_owned_input_poll()
  timing=(C.c_uint64*2)();stage=(C.c_uint64*3)();hud_stage=(C.c_uint64*3)()
  weight=samples.weight*i/119.0
  draw_begin=time.perf_counter_ns()
  assert api_timed(frame,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,samples.lower,samples.upper,15136,weight,timing)==0
  draw_end=time.perf_counter_ns()
  assert d.nf_owned_gpu_sky_draw_stages(stage)==0 and d.nf_owned_gpu_sky_hud_stages(hud_stage)==0
  deadline=origin+int((i+1)*1e9/60);remaining=(deadline-time.perf_counter_ns())/1e9
  if remaining>0:time.sleep(remaining)
  present_begin=time.perf_counter_ns();present_time=C.c_uint64();present_stages=(C.c_uint64*3)();assert d.nf_owned_gpu_present_timed(h[6],C.byref(present_time))==0;assert d.nf_owned_gpu_present_stages(present_stages)==0
  records.append(dict(draw_begin_ns=draw_begin,draw_end_ns=draw_end,present_begin_ns=present_begin,present_ns=time.perf_counter_ns(),present_ms=present_time.value/1e6,present_stages_ms=[x/1e6 for x in present_stages],index=i,sky_weight=weight,elapsed_ms=timing[0]/1e6,thread_cpu_ms=timing[1]/1e6,draw_stages_ms=[x/1e6 for x in stage],hud_stages_ms=[x/1e6 for x in hud_stage],cache=counters()))
 # After the paced run, read seven points from the same-pose continuous sky sweep.
 # These readbacks are deliberately outside the timing window.
 sky_pixel_sweep=[];previous_sky=None;out=C.create_string_buffer(3840*2160*3)
 for j in range(7):
  weight=samples.weight*j/6.0
  assert api(frame,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,samples.lower,samples.upper,15136,weight)==0
  assert d.nf_owned_gpu_read(out,len(out))==0
  raw=out.raw;changed=None
  if previous_sky is not None:
   a=np.frombuffer(previous_sky,dtype=np.uint8).reshape(-1,3);b=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3)
   changed=int(np.count_nonzero(np.any(a!=b,axis=1)))
   if changed==0:raise AssertionError('Continuous sky weight failed to change any full-scene output pixels')
  sky_pixel_sweep.append(dict(index=j,weight=weight,sha256=hashlib.sha256(raw).hexdigest(),changed_pixels_from_previous=changed))
  previous_sky=raw
 assert draw(frame)==reference,'Repeated draw altered fullscene pixels'
finally:
 stop_producer.set()
 if producer_thread.ident is not None:producer_thread.join(10)
 assert not producer_thread.is_alive()
 producer.nf_native_live_scene_count.restype=C.c_uint;native_capture_count=int(producer.nf_native_live_scene_count());assert native_capture_count==0 if mode.disable_capture else native_capture_count>0,'Unexpected native capture scene count'
 producer.nf_close();assert d.nf_owned_gpu_close()
assert not producer_errors,producer_errors
elapsed=sorted(r['elapsed_ms'] for r in records)
gaps=[(b['present_ns']-a['present_ns'])/1e6 for a,b in zip(records,records[1:])]
result=dict(capture_enabled=not mode.disable_capture,native_capture_scenes=native_capture_count,original_producer_updates=len(producer_rows),producer_update_timings=producer_rows,present_max_ms=max(r['present_ms'] for r in records),gap_max_ms=max(gaps),gaps_over_33_33ms=sum(x>1000/30 for x in gaps),draws=len(records),median_ms=statistics.median(elapsed),p95_ms=elapsed[int(.95*(len(elapsed)-1))],max_ms=max(elapsed),over_16_67ms=sum(x>1000/60 for x in elapsed),records=records,pixel_repeat_exact=True,sky_weight_sequence='linear 0..captured source-pair weight over 120 paced frames',continuous_sky_pixel_sweep=sky_pixel_sweep,scope='Fixed complete source scene; sky weight changes on every timed output frame and seven same-pose 4K pixel readbacks confirm visible output changes. Original producer advances at GBA period in a separate thread. CPU presentation timestamps only; no full game-scene motion, physical scanout or end-user display certification.')
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-capture-producer-20261006');out=out/('disabled-' if mode.disable_capture else 'enabled-')/str(time.time_ns());out.mkdir(parents=True,exist_ok=True);(out/'tests.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ('records','producer_update_timings')})
