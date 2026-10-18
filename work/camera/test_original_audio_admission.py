"""Real original PCM into future device queue; retire before audible output."""
import ctypes as C,time,json,hashlib
from pathlib import Path
from owned_audio_stream import OwnedAudioStream
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace('visibility-probe-wide.dll','sky-caller-probe.dll')
exec(compile(setup,'audio-admission-setup','exec'))
d.nf_original_audio_info.argtypes=[C.c_void_p]
o=C.CDLL(str(Path('work/camera/owned-audio-output.dll').resolve()));o.nf_audio_output_now.restype=C.c_uint64
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
a=None
try:
 a=OwnedAudioStream(d,o,7,capacity=2)
 limit=time.monotonic()+5
 while not a.status()[3]:
  assert time.monotonic()<limit;time.sleep(.002)
 origin=o.nf_audio_output_now()+10000000000
 records=[]
 for refresh in range(3):
  d.nf_frame(1);accepted=a.pump(refresh,origin,12);records.append({'refresh':refresh,'accepted':accepted,'next_sample':a.first_sample})
 assert [r['accepted'] for r in records]==[True,True,False]
 before=(C.c_uint64*3)();assert d.nf_original_audio_info(before)
 pending=a.pending;payload=C.string_at(pending[0],pending[1]*4);assert any(payload)
 for i in range(10):assert not a.pump(3+i,origin,12) and a.pending is pending
 after=(C.c_uint64*3)();assert d.nf_original_audio_info(after);assert list(before)==list(after),'Retry drained more original PCM'
 full=a.status();assert full[6]==2 and full[8]==0
 a.retire();limit=time.monotonic()+5
 while a.status()[2]!=2:
  assert time.monotonic()<limit;time.sleep(.002)
 flushed=a.status();assert flushed[6]==0 and flushed[8]==0 and a.pending is None
 assert a.resume()
 result={'result':'PASS','records':records,'full_status':full,'flushed_status':flushed,'original_info_before_retry':list(before),'original_info_after_retry':list(after),'pending_pcm_sha256':hashlib.sha256(payload).hexdigest(),'scope':'Three actual game updates; two future queued chunks plus retained pending chunk, ten retries without further original PCM reads, retirement before any submission. No audible playback or audiovisual sync proof'}
finally:
 if a:a.close()
 d.nf_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-audio-stream-20261006');cp.mkdir(parents=True,exist_ok=True);(cp/'original-admission.json').write_text(json.dumps(result,indent=2));print('PASS real original PCM admission, ten retained retries, device flush')
