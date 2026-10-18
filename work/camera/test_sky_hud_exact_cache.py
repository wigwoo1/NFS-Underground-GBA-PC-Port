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
checks=[]
try:
 first=draw(frame);before=counters();assert draw(frame)==first;after=counters();assert after[0]==before[0]+1
 checks.append('exact repeat hit')
 header=struct.unpack_from('<6I2Q',frame);hud=40+header[2];text=hud+header[3]+header[4]
 for label,offset in [('palette',hud+128+32768),('oam',hud+128+32768+1024),('obj_vram',hud+128),('text_index',text),('text_coverage',text+38400)]:
  changed=bytearray(frame);changed[offset]^=1;changed=bytes(changed);before=counters();cached=draw(changed);after=counters();assert after[1]==before[1]+1,(label,before,after)
  assert crt._putenv(b'NF_SKY_HUD_NO_CACHE=1')==0;reference=draw(changed);assert cached==reference,label;assert crt._putenv(b'NF_SKY_HUD_NO_CACHE=')==0;checks.append(label+' miss and exact uncached pixels')
 changed=bytearray(frame);struct.pack_into('<Q',changed,24,header[6]+1);before=counters();draw(bytes(changed));assert counters()[1]==before[1]+1;checks.append('epoch miss')
 assert d.nf_owned_gpu_close();before=None;draw(frame);before=counters();assert draw(frame)==first;assert counters()[0]==before[0]+1;checks.append('context reopen exact then hit')
finally:
 crt._putenv(b'NF_SKY_HUD_NO_CACHE=');assert d.nf_owned_gpu_close()
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-hud-exact-cache-20261006');(out/'cache-tests.json').write_text(json.dumps(dict(result='PASS',checks=checks),indent=2));print('PASS exact HUD cache',len(checks))
