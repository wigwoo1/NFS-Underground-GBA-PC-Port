"""Bounded busy-only retries preserve samples; capacity never spin-waits."""
import ctypes as C,json
from pathlib import Path
exec(compile(Path('work/camera/test_owned_audio_stream.py').read_text().split('b=Bridge();')[0],'fixture','exec'))
import owned_audio_stream as stream_module
yields=[];original_sleep=stream_module.time.sleep;stream_module.time.sleep=lambda seconds:yields.append(seconds)
b=Bridge();o=Output();o.results=[-3,-3,1];a=OwnedAudioStream(b,o,7)
assert a.pump_retry_busy(10,1000000000,12) and b.reads==1 and len(o.calls)==3 and len(set(o.calls))==1 and a.first_sample==800
b2=Bridge();o2=Output();o2.results=[-4,1];a2=OwnedAudioStream(b2,o2,7)
assert not a2.pump_retry_busy(10,1000000000,12) and len(o2.calls)==1 and a2.pending is not None
b3=Bridge();o3=Output();o3.results=[-3]*4;a3=OwnedAudioStream(b3,o3,7)
assert not a3.pump_retry_busy(10,1000000000,12) and len(o3.calls)==4 and b3.reads==1 and a3.first_sample==0
assert yields==[0]*5,'Busy retries must only yield, bounded; full must not wait'
stream_module.time.sleep=original_sleep
for stream in (a,a2,a3):stream.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-boundary-gap-20261006');(cp/'busy-retry-tests.json').write_text(json.dumps({'result':'PASS','checks':['three busy retries preserve owned bytes/deadline/read count','full rejects after one attempt','persistent busy bounded to four attempts']},indent=2));print('PASS bounded busy-only retry')
