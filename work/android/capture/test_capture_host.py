"""Borrowed-core observer fidelity test. Capture is diagnostic, no renderer."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,struct
a=argparse.ArgumentParser()
for name in ("library","runtime","reference","report"):a.add_argument("--"+name,type=Path,required=True)
a=a.parse_args()
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):
 d=C.CDLL(str(a.library))
 d.nfa_core_open.argtypes=[C.c_char_p];d.nfa_core_open.restype=C.c_void_p
 d.nfa_core_close.argtypes=[C.c_void_p]
 d.nfa_core_load_state.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 d.nfa_core_step.argtypes=[C.c_void_p,C.c_uint32]
 d.nfa_core_pause.argtypes=[C.c_void_p,C.c_int]
 d.nfa_core_timing.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)]
 d.nfa_core_pixels.argtypes=[C.c_void_p];d.nfa_core_pixels.restype=C.c_void_p
 d.nfa_core_read_audio.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];d.nfa_core_read_audio.restype=C.c_size_t
 d.nfa_core_capture_enable.argtypes=[C.c_void_p,C.c_int]
 d.nfa_core_capture_stats.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)]
 d.nfa_core_capture_copy.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];d.nfa_core_capture_copy.restype=C.c_size_t
 reference=json.loads(a.reference.read_text());ref=reference["original_frame_hashes"];state=(a.runtime/"checkpoint.state").read_bytes()
 guard=(C.c_uint64*8)(*[77]*8);assert not d.nfa_core_capture_stats(None,guard) and list(guard)==[77]*8
 h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
 packets=[];audio=hashlib.sha256();pcm=(C.c_int16*8192)();last=0
 def timing():
  t=(C.c_uint64*4)();assert d.nfa_core_timing(h,t);return list(t)
 def stats():
  t=(C.c_uint64*8)();assert d.nfa_core_capture_stats(h,t);return list(t)
 try:
  assert d.nfa_core_load_state(h,state,len(state))
  assert d.nfa_core_capture_enable(h,1)
  begin=timing()
  for i,expected in enumerate(ref):
   assert d.nfa_core_step(h,1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0))==1
   assert hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected,i
   now=timing();assert now==[16777216,280896,begin[2]+i+1,i+1]
   n=d.nfa_core_read_audio(h,pcm,4096);audio.update(C.string_at(pcm,n*4))
   s=stats();assert s[4:6]==[0,0],("capture rejected scene",i,s)
   if s[3]!=last:
    assert s[3]==last+1
    size=d.nfa_core_capture_copy(h,None,0);assert size>92
    out=C.create_string_buffer(size);assert d.nfa_core_capture_copy(h,out,size)==size
    raw=out.raw;head=struct.unpack_from("<8I",raw)
    assert head[0]==0x3150534e and head[1] in (1,2) and head[2:4]==(size,5) and head[5]<=head[6]<=now[2] and head[7] in (0,1) and head[4]==s[7],(head,now,s)
    if not packets:
     C.memset(out,165,size);assert not d.nfa_core_capture_copy(h,out,size-1) and out.raw==b"\xa5"*size
    packets.append({"frame":i+1,"epoch":s[1],"serial":head[4],"bytes":size,"sha256":hashlib.sha256(raw).hexdigest()})
    last=s[3]
  assert [[p["epoch"],p["bytes"],p["sha256"]] for p in packets]==reference["packets"]
  assert audio.hexdigest()=="eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"
  before=timing();observed=stats();assert d.nfa_core_pause(h,1)
  for _ in range(10):assert d.nfa_core_step(h,1)==2 and timing()==before and stats()==observed
  assert d.nfa_core_pause(h,0)
  epoch=stats()[1];assert d.nfa_core_load_state(h,state,len(state))
  assert stats()[1]>epoch and not d.nfa_core_capture_copy(h,None,0)
  for expected in ref[:16]:
   assert d.nfa_core_step(h,1)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected
  assert stats()[3]>observed[3] and d.nfa_core_capture_copy(h,None,0)>92
  newest=[p for p in packets if p["frame"]<=16][-1]
  n=d.nfa_core_capture_copy(h,None,0);restored=C.create_string_buffer(n)
  assert d.nfa_core_capture_copy(h,restored,n)==n and hashlib.sha256(restored.raw).hexdigest()==newest["sha256"]
  assert d.nfa_core_capture_enable(h,0) and stats()==[0]*8
  for expected in ref[16:26]:
   assert d.nfa_core_step(h,1)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected
  assert d.nfa_core_capture_enable(h,1)
 finally:d.nfa_core_close(h)
 h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
 try:
  assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1)
  for expected in ref[:16]:assert d.nfa_core_step(h,1)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected
 finally:d.nfa_core_close(h)
 report={"result":"PASS_BORROWED_CORE_CAPTURE_HOST","original_frame_hashes":len(ref),"native_packets":len(packets),"native_packets_match_preserved_pc_reference":True,
 "audio_sha256":audio.hexdigest(),"pause_preserved":True,"state_load_invalidated_epoch":True,"capture_resumed_after_state_load":True,"detach_restored_original_frames":True,
 "close_reopen_capture":True,"short_buffer_atomic":True,"packets":packets,"android_runtime":False,"rendering":False}
 a.report.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="packets"},indent=2))
