"""Try-pop ownership/paused/epoch guards and deterministic foreign lock collision."""
import ctypes as C,time,threading,struct,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t
# Fixture includes exact production C plus lock injection, never used by launcher.
d=C.CDLL(str(Path('work/camera/owned-handoff-try-pop-test.dll').resolve()))
for name,args,r in (('create',[U],P),('push',[P,P,Z],C.c_int),('pause',[P,C.c_uint],C.c_int),('epoch',[P,U],C.c_int),('destroy',[P],None)):
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=r
d.nf_owned_frame_free.argtypes=[P];d.nf_test_hold_queue.argtypes=[P,P,P]
fn=C.PYFUNCTYPE(C.c_int,P,P,P,P)(C.cast(d.nf_owned_handoff_try_pop_token,P).value)
k=C.WinDLL('kernel32');k.CreateEventW.argtypes=[P,C.c_int,C.c_int,C.c_wchar_p];k.CreateEventW.restype=P;k.WaitForSingleObject.argtypes=[P,C.c_uint];k.SetEvent.argtypes=[P];k.CloseHandle.argtypes=[P]
q=d.nf_owned_handoff_create(3);assert q
out=P(123);size=Z(456);gen=U(789)
def take(expected):
 before=(out.value,size.value,gen.value);result=fn(q,C.byref(out),C.byref(size),C.byref(gen));assert result==expected
 if result!=1:assert before==(out.value,size.value,gen.value)
ready=k.CreateEventW(None,1,0,None);release=k.CreateEventW(None,1,0,None);assert ready and release
try:
 take(0);assert fn(None,C.byref(out),C.byref(size),C.byref(gen))==-1
 text=160*34944;frame=struct.pack('<6I2Q',0x3346474e,10,0,text,76800,76800,3,10*280896)+bytes(text+153600)
 assert d.nf_owned_handoff_push(q,frame,len(frame))
 t=threading.Thread(target=lambda:d.nf_test_hold_queue(q,ready,release));t.start();assert k.WaitForSingleObject(ready,1000)==0
 begin=time.perf_counter_ns();take(-2);elapsed=time.perf_counter_ns()-begin
 assert not k.WaitForSingleObject(release,0)==0,'Fixture not actually holding lock'
 k.SetEvent(release);t.join(5);assert not t.is_alive()
 take(1);assert size.value==len(frame) and gen.value==1 and C.string_at(out,size.value)==frame;d.nf_owned_frame_free(out);out.value=123
 assert d.nf_owned_handoff_push(q,frame,len(frame));assert d.nf_owned_handoff_pause(q,1);take(0)
 assert d.nf_owned_handoff_pause(q,0);take(0)
 assert d.nf_owned_handoff_epoch(q,4);frame4=bytearray(frame);struct.pack_into('<Q',frame4,24,4);assert d.nf_owned_handoff_push(q,bytes(frame4),len(frame4));take(1);assert gen.value>1;d.nf_owned_frame_free(out)
finally:k.SetEvent(release);d.nf_owned_handoff_destroy(q);k.CloseHandle(ready);k.CloseHandle(release)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-try-pop-20261006');(cp/'tests.json').write_text(json.dumps({'result':'PASS','busy_call_elapsed_ns':elapsed,'checks':['held foreign queue lock returns busy without waiting/mutating outputs','exact independent native copy transfer','paused and empty reject unchanged','new epoch generation preserved','invalid rejection']},indent=2));print('PASS nonblocking owned token pop',elapsed,'ns busy')
