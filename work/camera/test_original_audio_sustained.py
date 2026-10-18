"""Original-cycle PCM/device pacing without graphics; playback diagnostic."""
import ctypes as C,time,json
from pathlib import Path
from owned_audio_stream import OwnedAudioStream
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace('visibility-probe-wide.dll','sky-caller-probe.dll')
exec(compile(setup,'sustained-audio-setup','exec'))
o=C.CDLL(str(Path('work/camera/owned-audio-output.dll').resolve()));o.nf_audio_output_last_submission.argtypes=[C.c_void_p,C.c_void_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
a=None;records=[];failure=None
try:
 a=OwnedAudioStream(d,o,7,minimum_frames=2048);limit=time.monotonic()+5
 while not a.status()[3]:assert time.monotonic()<limit;time.sleep(.002)
 origin=time.perf_counter_ns();updates=720
 for i in range(updates):
  deadline=origin+((i+1)*280896*1000000000+16777215)//16777216
  while True:
   left=deadline-time.perf_counter_ns()
   if left<=0:break
   time.sleep(min(.002,left/1e9))
  begin=time.perf_counter_ns();d.nf_frame(1);end=time.perf_counter_ns()
  accepted=a.pump(i,origin,12);state=a.status();event=(C.c_uint64*8)();assert o.nf_audio_output_last_submission(a.handle,event)
  records.append(dict(update=i,original_deadline=deadline,begin=begin,end=end,accepted=accepted,status=state,submission=list(event)))
  if not accepted:failure=dict(result=a.last_result,update=i,pending_frames=a.pending[1] if a.pending else None);break
 elapsed=time.perf_counter_ns()-origin
 final=a.status()
finally:
 if a:a.close()
 d.nf_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/audio-isolation-20261006');cp.mkdir(parents=True,exist_ok=True)
result={'result':'FAILED' if failure else 'PASS','failure':failure,'updates':len(records),'elapsed_ns':elapsed,'simulated_ns':len(records)*280896*1000000000/16777216,'max_occupied':max(r['status'][6] for r in records),'final_status':final,'records':records,'scope':'Original game core with actual PCM/device output and original-cycle pacing, graphics/capture disabled. No fullscene timing or AVsync proof.'}
(cp/'sustained-batched.json').write_text(json.dumps(result,indent=2));print({k:result[k] for k in ('result','failure','updates','max_occupied','elapsed_ns','simulated_ns')})
