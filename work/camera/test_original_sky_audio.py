"""Original-clock deterministic PCM and game-memory parity; no device playback."""
import ctypes as C,json,hashlib,threading,struct,wave
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-original-audio-stream-20261006');cp.mkdir(parents=True,exist_ok=True)
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace('visibility-probe-wide.dll','sky-caller-probe.dll')
exec(compile(setup,'audio-setup','exec'))
old=C.CDLL(str((cp/'bridge-before-audio.dll').resolve()))
for dll in (old,d):
 dll.nf_init.argtypes=[C.c_char_p,C.c_char_p];dll.nf_state.argtypes=[C.c_char_p,C.c_int];dll.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
d.nf_original_audio_read.argtypes=[C.c_void_p,C.c_uint];d.nf_original_audio_available.argtypes=[C.c_void_p];d.nf_original_audio_info.argtypes=[C.c_void_p]
regions=((0x02000000,0x40000),(0x03000000,0x8000),(0x06000000,0x18000),(0x05000000,1024),(0x07000000,1024));frames=180;checks=0

def run(dll,label,rate=None):
 global checks
 assert dll.nf_init(str(rom).encode(),b'') and dll.nf_state(str(state).encode(),0)
 pcm=bytearray();total=0;available=(C.c_uint*2)();buf=(C.c_int16*8192)()
 try:
  if rate:
   assert dll.nf_original_audio_configure(rate)
   assert not dll.nf_original_audio_configure(12345)
   info=(C.c_uint64*3)();assert dll.nf_original_audio_info(info);assert tuple(info)==(rate,16777216,0)
   canary=(C.c_int16*8)(*([1234]*8));assert dll.nf_original_audio_read(canary,4097)==-1 and list(canary)==[1234]*8;checks+=1
   rejected=[]
   t=threading.Thread(target=lambda:rejected.append(dll.nf_original_audio_read(buf,10)));t.start();t.join(5);assert not t.is_alive() and rejected==[-1];checks+=1
  for update in range(frames):
   dll.nf_frame(1|(32 if update>=40 else 0))
   if rate:
    assert dll.nf_original_audio_available(available) and available[0]==available[1]
    while available[0]:
     n=dll.nf_original_audio_read(buf,4096 if update%2 else 113);assert n>0;pcm.extend(C.string_at(buf,n*4));total+=n
     assert dll.nf_original_audio_available(available)
  hashes=[]
  for index,(address,size) in enumerate(regions):
   path=cp/(label+'-region-'+str(index)+'.bin');dll.nf_dump(str(path).encode(),address,size);payload=path.read_bytes();assert len(payload)==size;hashes.append(hashlib.sha256(payload).hexdigest())
  if rate:
   assert dll.nf_original_audio_info(info) and info[2]==total
   expected=frames*280896*rate/16777216
   assert abs(total-expected)<rate/30,(total,expected)
   samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm);assert any(samples),'Original PCM is all silent'
   assert dll.nf_original_audio_clear() and dll.nf_original_audio_available(available) and list(available)==[0,0]
   assert dll.nf_original_audio_read(buf,4096)==0;checks+=1
  return dict(label=label,rate=rate,frames=frames,pcm_frames=total,pcm_sha256=hashlib.sha256(pcm).hexdigest(),game_memory_hashes=hashes,pcm=bytes(pcm))
 finally:dll.nf_close()
baseline=run(old,'reference');first=run(d,'48000-a',48000);second=run(d,'48000-b',48000);third=run(d,'44100',44100)
assert first['pcm']==second['pcm'] and first['pcm_frames']==second['pcm_frames'];assert all(x['game_memory_hashes']==baseline['game_memory_hashes'] for x in (first,second,third))
assert d.nf_original_audio_read((C.c_int16*2)(),1)==-1;checks+=1
with wave.open(str(cp/'original-race-48000.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(first['pcm'])
for x in (baseline,first,second,third):x.pop('pcm')
result=dict(result='PASS',runs=[baseline,first,second,third],negative_and_clear_checks=checks,scope='Original 180 game updates, deterministic48kHz stereoPCM,44.1kHz rate/count checks, full EWRAM/IWRAM/VRAM/palette/OAM parity vs preserved bridge; offline capture only, no live device/audio-video sync certification')
(cp/'tests.json').write_text(json.dumps(result,indent=2));print(result)
