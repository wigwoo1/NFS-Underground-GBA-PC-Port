import ctypes as C,json
from pathlib import Path
from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
original=C.CDLL
loads=[]
def load(path,*args,**kwargs):
 if Path(path).name.startswith('owned-gpu-source-'):
  path=str(Path(path).with_name('owned-gpu-input-message-candidate.dll'));loads.append(path)
 return original(path,*args,**kwargs)
C.CDLL=load;session=None
try:
 session=NativeSourceSession();s=session.source;assert len(loads)==1
 s.nf_owned_input_poll_timed.argtypes=[C.c_void_p];s.nf_owned_input_message_profile.argtypes=[C.c_void_p]
 elapsed=C.c_uint64();assert s.nf_owned_input_poll_timed(C.byref(elapsed))==1
 u=C.WinDLL('user32');u.PostMessageW.argtypes=[C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t];u.PostMessageW.restype=C.c_int
 assert u.PostMessageW(session.consumer.window,0x8008,42,17)
 assert s.nf_owned_input_poll_timed(C.byref(elapsed))==1
 profile=(C.c_uint64*6)();assert s.nf_owned_input_message_profile(profile)==1
 assert profile[5]>=1 and profile[2]>=profile[1] and profile[0]==0x8008 and profile[3:5]==[42,17],list(profile)
 assert s.nf_owned_input_message_profile(None)==0
 report=dict(result='PASS_ACTUAL_NATIVE_MESSAGE_TIMING',profile=list(profile),poll_ns=elapsed.value,scope='HarmlessWM_APP+8 posted to private diagnostic window; verifies native message identity/payload/timestamps, not historicmodalstall subtype.')
 Path('work/camera/prototype-runs/input-message-component-20261010.json').write_text(json.dumps(report,indent=2));print(report)
finally:
 if session is not None:session.close();assert session.source.nf_owned_gpu_contexts()==0
 C.CDLL=original
