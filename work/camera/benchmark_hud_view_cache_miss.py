"""Fixed full-scene sky draw cost; excludes game logic and physical scanout."""
import ctypes as C,json,time,statistics
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text());folder=Path(items[0]['folder'])
frame=(folder/'frame.bin').read_bytes();buf=C.create_string_buffer(frame)
older=SkyBoundary.decode((folder/'older-sky.bin').read_bytes());newer=SkyBoundary.decode((folder/'newer-sky.bin').read_bytes())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();origin=older.asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
arrays={n:(C.c_double*(len((folder/(n+'.bin')).read_bytes())//8)).from_buffer_copy((folder/(n+'.bin')).read_bytes()) for n in ('camera','models','bounds')}
crt=C.CDLL('msvcrt');assert crt._putenv(b'NF_SKY_HUD_NO_CACHE=1')==0
finish=C.WinDLL('opengl32').glFinish;results=[]
for trial,names in enumerate((('owned-sky-spatial-runs.dll','owned-sky-hud-view-candidate.dll'),('owned-sky-hud-view-candidate.dll','owned-sky-spatial-runs.dll'))):
 for name in names:
  d=C.CDLL(str((Path('work/camera')/name).resolve()));f=d.nf_owned_gpu_draw_scene_clips_sky;f.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double]
  assert d.nf_owned_gpu_window(0)==0;rows=[]
  try:
   for tick in range(35):
    sky=asset.sample_continuous(older,newer,(tick%30)/30);lo=C.create_string_buffer(sky.lower);hi=C.create_string_buffer(sky.upper)
    begin=time.perf_counter_ns();rc=f(buf,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],len(arrays['bounds'])//4,lo,hi,15136,sky.weight);draw=time.perf_counter_ns();assert rc==0,rc;finish();end=time.perf_counter_ns()
    if tick>=5:rows.append(dict(draw_ms=(draw-begin)/1e6,draw_and_finish_ms=(end-begin)/1e6))
  finally:assert d.nf_owned_gpu_close()
  def stats(key):
   v=sorted(r[key] for r in rows);return dict(median=statistics.median(v),p95=v[math.ceil(.95*len(v))-1],max=max(v))
  import math
  results.append(dict(trial=trial,renderer=name,samples=len(rows),draw_ms=stats('draw_ms'),draw_and_finish_ms=stats('draw_and_finish_ms'),rows=rows))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-view-cache-miss-cost-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='MEASURED',results=results,scope='Forced HUD cache misses, fixed captured fullscene geometry with moving sky, alternate renderer order, CPU draw and draw+glFinish wall durations. Not GPU timestamp, live scheduling, fidelity or physical scanout proof.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps([{k:v for k,v in r.items() if k!='rows'} for r in results]))
