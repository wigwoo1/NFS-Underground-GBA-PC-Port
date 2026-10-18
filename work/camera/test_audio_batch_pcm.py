"""Exact actual game PCM comparison across batching thresholds."""
import ctypes as C,json,hashlib
from pathlib import Path
from owned_audio_stream import OwnedAudioStream
fake=Path('work/camera/test_owned_audio_stream.py').read_text().split('b=Bridge();')[0];exec(compile(fake,'fake-output','exec'))
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace('visibility-probe-wide.dll','sky-caller-probe.dll');exec(compile(setup,'pcm-batch-setup','exec'))
results=[]
for threshold in (1,2048):
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
 sink=Output();sink.results=[1]*1000;a=OwnedAudioStream(d,sink,7,minimum_frames=threshold)
 try:
  for i in range(180):d.nf_frame(1);assert a.pump(i,1000000000,12)
  # Explicit tail drain for exact capture comparison; live continues collecting.
  a.minimum_frames=1;assert a.pump(180,1000000000,12)
  pcm=b''.join(row[-1] for row in sink.calls)
  results.append(dict(threshold=threshold,frames=len(pcm)//4,chunks=len(sink.calls),sha256=hashlib.sha256(pcm).hexdigest()))
 finally:a.close();d.nf_close()
assert results[0]['frames']==results[1]['frames'] and results[0]['sha256']==results[1]['sha256'] and results[1]['chunks']<results[0]['chunks']
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/audio-isolation-20261006');(cp/'pcm-parity.json').write_text(json.dumps({'result':'PASS','runs':results,'scope':'Actual180originalupdates PCM bytes exact after explicit final tail drain; fake output sink, no AVsync proof'},indent=2));print('PASS exact PCM batching',results)
