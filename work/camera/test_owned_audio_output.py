"""Actual output device queue with inaudible samples; no game/AV certification."""
import ctypes as C,time,json,threading
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-audio-output-20261006');cp.mkdir(parents=True,exist_ok=True)
d=C.CDLL(str(Path('work/camera/owned-audio-output.dll').resolve()));P=C.c_void_p;U=C.c_uint64
for name,args,restype in (
 ('create',[U,C.c_uint,C.c_uint],P),('push',[P,U,U,U,U,U,P,C.c_uint],C.c_int),('retire',[P,U],U),('resume',[P,U,U],C.c_int),('status',[P,P],C.c_int),('last_submission',[P,P],C.c_int),('close',[P,C.c_uint],C.c_int),('pending_read',[P,U,U,U,P,C.c_uint,P],C.c_int)):
 f=getattr(d,'nf_audio_output_'+name);f.argtypes=args;f.restype=restype
d.nf_audio_output_now.restype=U
kernel=C.WinDLL('kernel32',use_last_error=True);kernel.OpenThread.argtypes=[C.c_uint,C.c_int,C.c_uint];kernel.OpenThread.restype=P;kernel.WaitForSingleObject.argtypes=[P,C.c_uint];kernel.CloseHandle.argtypes=[P]
checks=[];cycles=[]
def status(q):
 out=(U*14)();assert d.nf_audio_output_status(q,out);return list(out)
def until(q,predicate):
 end=time.monotonic()+5
 while time.monotonic()<end:
  s=status(q)
  if s[4]:raise RuntimeError('Audio device error '+str(s[4]))
  if predicate(s):return s
  time.sleep(.002)
 raise AssertionError('Audio worker state timeout '+str(s))
assert not d.nf_audio_output_create(0,48000,2) and not d.nf_audio_output_create(7,12345,2) and not d.nf_audio_output_create(7,48000,33);checks.append('invalid creation')
for cycle in range(3):
 q=d.nf_audio_output_create(7,48000,2);assert q;worker_handle=None
 try:
  start=until(q,lambda s:s[3]);assert start[12]!=start[13];worker_handle=kernel.OpenThread(0x00100000,0,start[13]);assert worker_handle
  deadline=d.nf_audio_output_now()+1000000000
  original=(C.c_int16*800)(*(i-400 for i in range(800)));copy=(C.c_int16*800)();n=C.c_uint(999)
  assert d.nf_audio_output_push(q,7,1,10,0,deadline,original,400)==1
  assert d.nf_audio_output_push(q,7,1,11,400,deadline,original,400)==1
  filled=status(q);assert filled[6]==2 and filled[7]==800 and filled[8]==0
  assert d.nf_audio_output_push(q,7,1,12,800,deadline,original,400)==-4
  original[0]=999
  assert d.nf_audio_output_pending_read(q,7,1,0,copy,400,C.byref(n)) and n.value==400 and copy[0]==-400
  before=bytes(copy);n.value=999;assert not d.nf_audio_output_pending_read(q,7,1,0,copy,399,C.byref(n)) and bytes(copy)==before and n.value==999
  for epoch,generation,first in ((8,1,800),(7,2,800),(7,1,123)):
   result=d.nf_audio_output_push(q,epoch,generation,12,first,deadline,original,400);assert result==(-1 if first==123 else -2)
  foreign=[];t=threading.Thread(target=lambda:foreign.append(d.nf_audio_output_push(q,7,1,12,800,deadline,original,400)));t.start();t.join(5);assert foreign==[-1] and not t.is_alive()
  after=status(q);assert after[6:12]==filled[6:12];checks.append('immutable copy/full/stale/order/foreign thread rejection cycle'+str(cycle))
  generation=d.nf_audio_output_retire(q,7);assert generation==2
  flushed=until(q,lambda s:s[2]==2);assert flushed[5] and flushed[6]==0 and flushed[10]==800 and flushed[8]==0
  assert not d.nf_audio_output_resume(q,7,1) and d.nf_audio_output_resume(q,7,2)
  silence=(C.c_int16*800)();target=d.nf_audio_output_now()+30000000
  assert d.nf_audio_output_push(q,7,2,20,0,target,silence,400)==1
  assert d.nf_audio_output_push(q,7,1,21,400,target,silence,400)==-2
  played=until(q,lambda s:s[9]>=400);assert played[8]==400 and played[9]==400 and played[6]==0
  event=(U*8)();assert d.nf_audio_output_last_submission(q,event);assert list(event[:6])==[7,2,20,0,400,target] and event[6]>=target and event[7]>=event[6];checks.append('tagged deadline/write/device completion')
  generation=d.nf_audio_output_retire(q,8);assert generation==3;until(q,lambda s:s[2]==3)
  assert not d.nf_audio_output_retire(q,7) and not d.nf_audio_output_resume(q,7,3) and d.nf_audio_output_resume(q,8,3)
  assert d.nf_audio_output_push(q,7,3,30,0,target,silence,400)==-2
  cycles.append(dict(initial=start,flushed=flushed,submission_event=list(event),device_completed=played,final=status(q)))
 finally:
  assert d.nf_audio_output_close(q,5000),'Audio resources retained after shutdown'
  if worker_handle:assert kernel.WaitForSingleObject(worker_handle,1000)==0;kernel.CloseHandle(worker_handle)
result=dict(result='PASS',cycles=cycles,checks=checks,scope='Actual WinMM device, borrowed input copied, bounded nonblocking admission, epoch/generation/order guards, future buffers retired before playback, silent deadline output and device completion, three worker joins. No audible game playback, scanout or audio-video sync certification')
(cp/'tests.json').write_text(json.dumps(result,indent=2));print('PASS owned audio output',len(cycles),'cycles',len(checks),'checks')
