import argparse
options=argparse.ArgumentParser();options.add_argument("--disable-capture",action="store_true");options.add_argument("--profile",action="store_true");options.add_argument("--capture-profile",action="store_true");mode=options.parse_args()
import ctypes as C,json,struct,hashlib
import numpy as np
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-replay-20261006');cp.mkdir(exist_ok=True)
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
if mode.profile or mode.capture_profile:
 producer.nf_native_wall_stage_profile_reset();producer.nf_native_wall_stage_profile_read.argtypes=[C.c_void_p]
 producer.nf_native_plan_profile_reset();producer.nf_native_plan_profile_read.argtypes=[C.c_void_p]
 producer.nf_capture_profile_enable(1);producer.nf_arm_stage_profile_enable(int(mode.profile))
 producer.nf_capture_profile_read.argtypes=[C.c_void_p];producer.nf_arm_stage_profile_read.argtypes=[C.c_void_p]
rows=[]
try:
 origin=time.perf_counter_ns();period=280896*1e9/16777216
 for index in range(120):
  delay=(origin+int(index*period)-time.perf_counter_ns())/1e9
  if delay>0:time.sleep(delay)
  begin=time.perf_counter_ns();native=(C.c_uint64*2)()
  assert original_timer.nf_original_update_timed(C.cast(producer.nf_frame,C.c_void_p),1,native)
  rows.append(dict(index=index,elapsed_ns=time.perf_counter_ns()-begin,native_elapsed_ns=int(native[0]),native_thread_cpu_ns=int(native[1])))
  if mode.profile or mode.capture_profile:
   measured=(C.c_uint64*6)();assert producer.nf_capture_profile_read(measured)
   rows[-1]['capture_stages_ns_calls']=list(measured)
 wall_totals=None
 if mode.profile or mode.capture_profile:
  measured=(C.c_uint64*4)();assert producer.nf_native_wall_stage_profile_read(measured);wall_totals=list(measured)
 plan_totals=None
 if mode.profile or mode.capture_profile:
  measured=(C.c_uint64*6)();assert producer.nf_native_plan_profile_read(measured);plan_totals=list(measured)
 profile_totals=None
 if mode.profile:
  measured=(C.c_uint64*6)();assert producer.nf_arm_stage_profile_read(measured);profile_totals=list(measured)
 producer.nf_native_live_scene_count.restype=C.c_uint;scenes=int(producer.nf_native_live_scene_count())
 assert scenes==0 if mode.disable_capture else scenes>0
finally:producer.nf_close()
result=dict(wall_stages_ns=wall_totals,plan_stages_ns_calls=plan_totals,arm_stages_ns_calls=profile_totals,capture_enabled=not mode.disable_capture,updates=len(rows),scenes=scenes,median_ms=statistics.median(x['elapsed_ns']/1e6 for x in rows),max_ms=max(x['elapsed_ns']/1e6 for x in rows),total_cpu_ms=sum(x['native_thread_cpu_ns'] for x in rows)/1e6,records=rows,scope='Original paced producer only, no window, GPU drawing, presentation or preparation; diagnostic not playable gameplay verification.')
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-producer-only-20261006')/str(time.time_ns());out.mkdir(parents=True);(out/'tests.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='records'})
