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
try:
 for item in items:
  folder=Path(item['folder']);frame=(folder/'frame.bin').read_bytes();h=struct.unpack_from('<6I2Q',frame)
  older=SkyBoundary.decode((folder/'older-sky.bin').read_bytes());newer=SkyBoundary.decode((folder/'newer-sky.bin').read_bytes());assert h[6]==older.epoch==newer.epoch and older.refresh<=h[1] and older.refresh<newer.refresh
  origin=older.asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);samples=asset.sample(older,newer,item['alpha']);assert samples.lower==(folder/'lower.bin').read_bytes() and samples.upper==(folder/'upper.bin').read_bytes() and samples.weight==item['weight']
  arrays={}
  for name in ('camera','models','bounds'):
   raw=(folder/(name+'.bin')).read_bytes();assert len(raw)%8==0;arrays[name]=(C.c_double*(len(raw)//8)).from_buffer_copy(raw)
  count=len(arrays['bounds'])//4;assert len(arrays['camera'])==12 and len(arrays['models'])==count*12
  assert api(frame,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,samples.lower,samples.upper,15136,samples.weight)==0
  out=C.create_string_buffer(3840*2160*3);assert d.nf_owned_gpu_read(out,len(out))==0;actual=out.raw;expected=(folder/'rgb.bin').read_bytes();assert actual==expected,('Full scene replay mismatch',folder,sum(a!=b for a,b in zip(actual,expected)))
  assert api(frame,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,samples.lower,samples.lower,15136,0)==0
  assert d.nf_owned_gpu_read(out,len(out))==0
  baseline=np.frombuffer(out.raw,dtype=np.uint8).reshape(2160,3840,3);image=np.frombuffer(actual,dtype=np.uint8).reshape(2160,3840,3)
  sx=np.floor((np.arange(3840)+.5-300)/13.5).astype(int);sy=np.floor((np.arange(2160)+.5)/13.5).astype(int)
  source=sy[:,None]*240+sx[None,:];allowed=(sx[None,:]>=0)&(sx[None,:]<240)&(source>=10560)&(source<25696)
  changed=np.any(image!=baseline,axis=2);assert not np.any(changed&~allowed),'Sky modified outside owned footprint'
  changed_count=int(changed.sum());assert changed_count>0
  checks.append(dict(folder=str(folder),epoch=h[6],refresh=h[1],geometry_records=count,changed_sky_output_pixels=changed_count,unchanged_outside_output_pixels=int((~allowed).sum()),exact_rgb_bytes=len(actual),rgb_sha256=hashlib.sha256(actual).hexdigest(),weight=samples.weight))
finally:assert d.nf_owned_gpu_close()
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual live fullscene wrap replay pixel exact with original ROM-derived indexed inputs/poses/clips. Establishes reproducibility, not independent game occlusion fidelity or timing'),indent=2));(cp/'test_live_sky_wrap_replay.py').write_text((p/'test_live_sky_wrap_replay.py').read_text());print('PASS live fullscene sky replays',len(checks))
