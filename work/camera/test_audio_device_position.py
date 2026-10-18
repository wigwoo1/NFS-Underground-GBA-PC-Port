"""WinMM-reported playback position, silent samples; not audible timing proof."""
import ctypes as C,time,json
from pathlib import Path
from owned_audio_stream import OwnedAudioStream
# Output ABI setup without configuring a game core.
o=C.CDLL(str(Path('work/camera/owned-audio-output.dll').resolve()));U=C.c_uint64;P=C.c_void_p
for name,args,result in (('position_enable',[P,C.c_int],C.c_int),('create',[U,C.c_uint,C.c_uint],P),('push',[P,U,U,U,U,U,P,C.c_uint],C.c_int),('status',[P,P],C.c_int),('retire',[P,U],U),('resume',[P,U,U],C.c_int),('position',[P,U,U,P],C.c_int),('close',[P,C.c_uint],C.c_int)):
 f=getattr(o,'nf_audio_output_'+name);f.argtypes=args;f.restype=result
o.nf_audio_output_now.restype=U
q=o.nf_audio_output_create(9,48000,2);assert q
rows=[]
def status():
 s=(U*14)();assert o.nf_audio_output_status(q,s);assert not s[4];return list(s)
def position(epoch,generation):
 p=(U*8)(*([123456]*8));ok=o.nf_audio_output_position(q,epoch,generation,p)
 if not ok:assert list(p)==[123456]*8
 return list(p) if ok else None
try:
 assert o.nf_audio_output_position_enable(q,1)
 limit=time.monotonic()+5
 while not status()[3]:assert time.monotonic()<limit;time.sleep(.002)
 assert position(10,1) is None and position(9,2) is None
 silence=(C.c_int16*2400)();target=o.nf_audio_output_now()+20000000
 assert o.nf_audio_output_push(q,9,1,10,0,target,silence,1200)==1
 limit=time.monotonic()+5
 while True:
  row=position(9,1)
  if row:
   assert row[0:2]==[9,1] and row[5]>=row[4] and row[6]==0
   if not rows or row[7]!=rows[-1][7]:rows.append(row)
  s=status()
  if s[9]>=1200 and row and row[3]>=1200:break
  assert time.monotonic()<limit,(s,row);time.sleep(.002)
 assert all(r[2]==2 for r in rows),'Driver returned non-sample units; cannot compare as frames'
 assert all(b[3]>=a[3] and b[7]>a[7] for a,b in zip(rows,rows[1:]))
 assert rows[-1][3]>=1200
 assert o.nf_audio_output_retire(q,10)==2
 assert position(9,1) is None and position(10,1) is None
 limit=time.monotonic()+5
 while status()[2]!=2:assert time.monotonic()<limit;time.sleep(.002)
 reset=None
 while reset is None:
  reset=position(10,2);assert time.monotonic()<limit;time.sleep(.002)
 assert reset[2]==2 and reset[3]==0 and reset[6]==0
 assert o.nf_audio_output_resume(q,10,2)
finally:assert o.nf_audio_output_close(q,5000)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/audio-device-position-20261006');cp.mkdir(parents=True,exist_ok=True)
result={'result':'PASS','position_rows':rows,'reset_position':reset,'scope':'Actual Windows mapper returns TIME_SAMPLES, monotone generation-local position reaches silent1200frames, query timestamps ordered, old epoch/generation rejects without writes, reset position zero. Driver-reported position is not hardware audible time; no AV scanout sync proof'}
(cp/'tests.json').write_text(json.dumps(result,indent=2));print('PASS device position',len(rows),'snapshots, reset zero')
