"""Generation onset gating and contiguous prequeue; silent device component."""
import ctypes as C,time,json
from pathlib import Path
s=Path('work/camera/test_owned_audio_output.py').read_text().split("assert not d.nf_audio_output_create")[0]
exec(compile(s,'continuous-output-setup','exec'))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/audio-continuous-queue-20261006');cp.mkdir(parents=True,exist_ok=True)
q=d.nf_audio_output_create(11,48000,2);assert q
try:
 until(q,lambda s:s[3]);target=d.nf_audio_output_now()+100000000
 silence=(C.c_int16*8192)();n=4096;second=target+(n*1000000000+47999)//48000
 assert d.nf_audio_output_push(q,11,1,10,0,target,silence,n)==1
 assert d.nf_audio_output_push(q,11,1,11,n,second,silence,n)==1
 assert status(q)[8]==0
 submitted=until(q,lambda s:s[8]==8192)
 event=(U*8)();assert d.nf_audio_output_last_submission(q,event)
 assert list(event[:6])==[11,1,11,4096,4096,second]
 assert event[6]<second,'Second block was not queued ahead'
 completed=until(q,lambda s:s[9]==8192)
 # Both blocks still play at 48 kHz rather than being consumed on submission.
 assert d.nf_audio_output_now()>=target+int(8192*1000000000/48000)-20000000
 assert d.nf_audio_output_retire(q,12)==2;until(q,lambda s:s[2]==2);assert d.nf_audio_output_resume(q,12,2)
 target2=d.nf_audio_output_now()+100000000
 assert d.nf_audio_output_push(q,12,2,20,0,target2,silence,400)==1
 time.sleep(.02);assert status(q)[8]==8192,'Reset generation bypassed new onset'
 until(q,lambda s:s[9]==8592)
 result={'result':'PASS','second_submission':list(event),'submitted_status':submitted,'completed_status':completed,'scope':'Silent contiguous8192frames: first onset gated, second4096frames queued before deadline, device completion duration retains48kHz timing, reset generation gates new onset. Not full live60fps/AVsync proof'}
finally:assert d.nf_audio_output_close(q,5000)
(cp/'component.json').write_text(json.dumps(result,indent=2));print('PASS continuous audio onset/prequeue/device rate/reset')
