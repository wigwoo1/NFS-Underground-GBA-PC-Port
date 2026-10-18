"""Deterministic admission/timing adapter test; fake device, no AV claim."""
import ctypes as C,json
from pathlib import Path
from owned_audio_stream import OwnedAudioStream
class Fn:
 def __init__(self,f):self.f=f
 def __call__(self,*a):return self.f(*a)
class Bridge:
 def __init__(self):
  self.reads=0;self.clears=0
  self.nf_original_audio_configure=Fn(lambda rate:rate==48000)
  self.nf_original_audio_available=Fn(self.available)
  self.nf_original_audio_read=Fn(self.read)
  self.nf_original_audio_clear=Fn(self.clear)
 def available(self,out):out[0]=out[1]=800;return 1
 def read(self,out,n):
  self.reads+=1
  for i in range(n*2):out[i]=i-800
  return n
 def clear(self):self.clears+=1;return 1
class Output:
 def __init__(self):
  self.results=[-4,-3,0,1,1];self.calls=[];self.ack=False
  self.nf_audio_output_create=Fn(lambda *a:123)
  self.nf_audio_output_push=Fn(self.push)
  self.nf_audio_output_retire=Fn(lambda h,e:2)
  self.nf_audio_output_resume=Fn(lambda *a:int(self.ack))
  self.nf_audio_output_close=Fn(lambda *a:1)
  self.nf_audio_output_status=Fn(lambda *a:1)
 def push(self,h,e,g,r,s,deadline,buf,n):
  self.calls.append((e,g,r,s,deadline,C.string_at(buf,n*4)))
  return self.results.pop(0)
b=Bridge();d=Output();a=OwnedAudioStream(b,d,7);origin=1000000000
for i in range(3):assert not a.pump(10+i,origin,12) and b.reads==1 and a.first_sample==0
assert a.pump(13,origin,12) and b.reads==1 and a.first_sample==800
assert len(set(d.calls))==1,'Retries changed owned samples or deadlines'
assert a.pump(14,origin,12) and b.reads==2 and a.first_sample==1600
expected_delay=(12*280896*1000000000+16777215)//16777216
assert d.calls[0][4]==origin+expected_delay
assert d.calls[-1][4]==origin+expected_delay+(800*1000000000+47999)//48000
# Retire a borrowed-independent pending buffer and require flush acknowledgement.
d.results=[-4];assert not a.pump(15,origin,12);a.retire();assert a.pending is None and a.first_sample==0 and b.clears==1
assert not a.pump(16,origin,12) and not a.resume();d.ack=True;assert a.resume()
d.results=[1];assert a.pump(17,origin+500000000,12)
assert d.calls[-1][:4]==(7,2,17,0) and d.calls[-1][4]==origin+500000000+expected_delay
try:a.pump(18,origin,-1)
except ValueError:pass
else:raise AssertionError('Negative delay accepted')
a.close()
try:a.pump(19,origin,12)
except RuntimeError:pass
else:raise AssertionError('Closed stream accepted')
result={'result':'PASS','checks':['immutable bounded pending retries','sample-contiguous admission','original-clock delayed deadlines','explicit retire discards pending and clears original buffer','flush acknowledgement before resume','new origin/generation after resume','negative delay and closed rejection'],'scope':'Timing/admission adapter component using fake output; no audible or scanout synchronization certification'}
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-audio-stream-20261006');cp.mkdir(parents=True,exist_ok=True);(cp/'tests.json').write_text(json.dumps(result,indent=2));print('PASS audio stream',len(result['checks']),'checks')
