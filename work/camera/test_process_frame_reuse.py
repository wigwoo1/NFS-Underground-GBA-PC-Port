import ctypes as C,json,struct
from pathlib import Path
from owned_process_preparation_service import ProcessSamples,encode_samples
r=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text())
checks=[]
for row in r:
 folder=Path(row['folder']);frame=(folder/'frame.bin').read_bytes();arrays=[(C.c_double*(len((folder/(name+'.bin')).read_bytes())//8)).from_buffer_copy((folder/(name+'.bin')).read_bytes()) for name in ('camera','models','bounds')]
 payload=encode_samples({.25:(frame,*arrays,{'captured':True}),.75:(frame,*arrays,{'captured':True})})
 ProcessSamples.reuse_immutable_frames=False;baseline=ProcessSamples(payload)
 ProcessSamples.reuse_immutable_frames=True;candidate=ProcessSamples(payload)
 try:
  for alpha in (.25,.75):
   a=baseline.sample(alpha);b=candidate.sample(alpha);assert a[0]==b[0] and a[4]==b[4] and all(bytes(x)==bytes(y) for x,y in zip(a[1:4],b[1:4]))
  assert candidate.sample(.25)[0] is candidate.sample(.75)[0]
  assert candidate.sample(.25)[1] is not candidate.sample(.75)[1]
  before=candidate.sample(.75)[1][0];candidate.sample(.25)[1][0]+=1;assert candidate.sample(.75)[1][0]==before
  checks.append(dict(folder=str(folder),exact_buffers=True,immutable_frame_shared=True,mutable_arrays_private=True))
 finally:baseline.close();candidate.close();assert not candidate.samples
ProcessSamples.reuse_immutable_frames=False
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/process-frame-reuse-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual captured scene frame and pose buffers duplicated within a bounded transported batch; live natural reuse frequency unproven'),indent=2));print('PASS',len(checks),'captured batches')
