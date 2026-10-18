"""Windows execution of the SAME portable C API; not Android-device testing."""
import argparse,ctypes as C,hashlib,json,os,random
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--library",type=Path,required=True)
p.add_argument("--runtime",type=Path,required=True)
p.add_argument("--reference",type=Path,required=True)
p.add_argument("--report",type=Path,required=True)
a=p.parse_args()
def sha(data):return hashlib.sha256(data).hexdigest()
class Touch(C.Structure):
 _fields_=[("ids",C.c_int32*16),("masks",C.c_uint32*16),("used",C.c_uint32)]
with os.add_dll_directory(r"C:\msys64\mingw64\bin"),os.add_dll_directory(str(a.library.parent)):
 d=C.CDLL(str(a.library))
 d.nfa_touch_clear.argtypes=[C.POINTER(Touch)]
 d.nfa_touch_set.argtypes=[C.POINTER(Touch),C.c_int32,C.c_uint32]
 d.nfa_touch_keys.argtypes=[C.POINTER(Touch)];d.nfa_touch_keys.restype=C.c_uint32
 t=Touch();contacts={};events=0
 def model_keys():
  keys=0
  for mask in contacts.values():keys|=mask
  if keys&48==48:keys&=~48
  if keys&192==192:keys&=~192
  return keys
 def event(pointer,mask):
  global events
  before=bytes(t);expected=pointer>=0 and mask&~255==0
  if expected and mask and pointer not in contacts and len(contacts)==16:expected=False
  assert bool(d.nfa_touch_set(C.byref(t),pointer,mask))==expected
  if expected:
   if mask:contacts[pointer]=mask
   else:contacts.pop(pointer,None)
  else:assert bytes(t)==before
  assert d.nfa_touch_keys(C.byref(t))==model_keys()
  events+=1
 # Every requested button, diagonals, drag, duplicate-held buttons and cancel.
 for mask in (1,2,4,8,16,32,64,128,16|64,32|128,1|2|4|8):
  event(3,mask);event(3,0)
 event(1,16);event(2,1);event(1,32);assert d.nfa_touch_keys(C.byref(t))==33
 event(3,1);event(2,0);assert d.nfa_touch_keys(C.byref(t))==33
 event(4,16);assert d.nfa_touch_keys(C.byref(t))==1
 d.nfa_touch_clear(C.byref(t));contacts.clear();assert d.nfa_touch_keys(C.byref(t))==0
 for i in range(16):event(i,1<<(i%8))
 event(100,1);event(-1,1);event(0,256)
 d.nfa_touch_clear(C.byref(t));contacts.clear()
 rng=random.Random(20261014)
 for _ in range(10000):
  event(rng.randrange(-1,25),rng.choice((0,1,2,4,8,16,32,64,128,17,65,80,160,255,256,1024)))
 d.nfa_touch_clear(C.byref(t));assert d.nfa_touch_keys(C.byref(t))==0
 # Typed opaque core interface.
 d.nfa_core_open.argtypes=[C.c_char_p];d.nfa_core_open.restype=C.c_void_p
 for name in ("nfa_core_close","nfa_core_pixels","nfa_core_state_size"):
  getattr(d,name).argtypes=[C.c_void_p]
 d.nfa_core_pixels.restype=C.c_void_p;d.nfa_core_state_size.restype=C.c_size_t
 d.nfa_core_step.argtypes=[C.c_void_p,C.c_uint32]
 d.nfa_core_pause.argtypes=[C.c_void_p,C.c_int]
 d.nfa_core_timing.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)]
 d.nfa_core_load_state.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 d.nfa_core_save_state.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 d.nfa_core_read_audio.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];d.nfa_core_read_audio.restype=C.c_size_t
 sentinel=(C.c_uint64*4)(77,77,77,77)
 assert not d.nfa_core_timing(None,sentinel) and list(sentinel)==[77]*4
 assert not d.nfa_core_open(None)
 assert not d.nfa_core_open(os.fsencode(a.runtime/"missing-game.gba"))
 h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
 hashes=[];pcm_frames=nonzero_chunks=0;audio_hash=hashlib.sha256()
 try:
  assert not d.nfa_core_open(os.fsencode(a.runtime/"game.gba")),"Only one live owner is supported"
  state=(a.runtime/"checkpoint.state").read_bytes();assert d.nfa_core_state_size(h)==len(state)
  assert d.nfa_core_load_state(h,state,len(state))
  def info():
   out=(C.c_uint64*4)();assert d.nfa_core_timing(h,out);return list(out)
  initial=info();assert initial[:2]==[16777216,280896] and initial[3]==0
  assert not d.nfa_core_load_state(h,state,len(state)-1) and info()==initial
  assert not d.nfa_core_step(h,1024) and info()==initial
  small=C.create_string_buffer(b"M"*32);before=small.raw
  assert not d.nfa_core_save_state(h,small,32) and small.raw==before
  assert d.nfa_core_pause(h,1)
  for _ in range(10):assert d.nfa_core_step(h,17)==2 and info()==initial
  assert d.nfa_core_read_audio(h,None,4096)==0
  assert d.nfa_core_pause(h,0)
  ref=json.loads(a.reference.read_text())["original_frame_hashes"]
  pcm=(C.c_int16*(4096*2))()
  for i in range(len(ref)):
   keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
   assert d.nfa_core_step(h,keys)==1
   stamp=info();assert stamp[2:]==[initial[2]+i+1,i+1]
   digest=sha(C.string_at(d.nfa_core_pixels(h),240*160*4))
   assert digest==ref[i],("original output differs",i,digest,ref[i])
   hashes.append(digest)
   n=d.nfa_core_read_audio(h,pcm,4096);assert 0<=n<=4096
   payload=C.string_at(pcm,n*4);audio_hash.update(payload)
   pcm_frames+=n;nonzero_chunks+=bool(any(payload))
  assert pcm_frames>0
  save=C.create_string_buffer(len(state));assert d.nfa_core_save_state(h,save,len(save))
  later=[]
  for _ in range(20):
   assert d.nfa_core_step(h,33)==1
   later.append(sha(C.string_at(d.nfa_core_pixels(h),240*160*4)))
  assert d.nfa_core_load_state(h,save,len(save))
  for expected in later:
   assert d.nfa_core_step(h,33)==1
   assert sha(C.string_at(d.nfa_core_pixels(h),240*160*4))==expected
 finally:d.nfa_core_close(h)
 assert not d.nfa_core_step(h,1) and not d.nfa_core_pixels(h)
 assert not d.nfa_core_timing(h,sentinel) and list(sentinel)==[77]*4
 h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
 try:
  assert d.nfa_core_load_state(h,state,len(state))
  for expected in hashes[:16]:
   assert d.nfa_core_step(h,1)==1
   assert sha(C.string_at(d.nfa_core_pixels(h),240*160*4))==expected
 finally:d.nfa_core_close(h)
 result=dict(result="PASS_HOST_COMPONENT",touch_reference_events=events,original_frame_hashes=hashes,
   original_frames_verified=len(hashes),step_cycles=280896,frequency=16777216,
   pause_did_not_advance=True,state_reload_replayed_frames=20,close_reopen_replayed_frames=16,
   stereo_pcm_frames=pcm_frames,audio_nonzero_chunks=nonzero_chunks,audio_sha256=audio_hash.hexdigest(),
   scope="Portable C API executed on Windows with the existing patched core archive. Android binaries, Activity/touch UI, audio output, device lifecycle, native 4K renderer and APK runtime are not verified here.")
 a.report.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!="original_frame_hashes"},indent=2))
