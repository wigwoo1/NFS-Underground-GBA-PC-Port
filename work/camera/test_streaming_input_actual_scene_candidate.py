"""Real shared mapping and actual byte-only scene transport parity."""
import sys,pickle,json,hashlib
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
s=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(s,'actual_scene_transport_setup','exec'))
from owned_scene_process_transport import pack,unpack
from owned_progressive_shared_transport_candidate import SharedInputConnection
from owned_streaming_input_write_candidate import send
class Pipe:
 def __init__(self):self.messages=[]
 def send(self,x):self.messages.append(x)
 def recv(self):return self.messages.pop(0)
packets=[pack(frame,scene) for frame,scene in zip(frames,scenes)]
alphas=tuple(x['alpha'] for x in expected if 0<x['alpha']<1)
requests=[('warm',0,packets[0]),(1,packets[0],scenes[0].identity,packets[1],alphas,True),(1,None,scenes[0].identity,packets[1],alphas,True)]
memory=SharedMemory(create=True,size=64*1024*1024);pipe=Pipe();writer=SharedInputConnection(pipe,memory,True);reader=SharedInputConnection(pipe,memory);checks=[]
try:
 for request in requests:
  baseline=pickle.dumps(request,protocol=5);send(writer,request);size=writer.last_write_profile['payload_bytes'];actual=bytes(memory.buf[:size]);assert actual==baseline
  detached=reader.recv();assert detached==request
  for packet in ([detached[2]] if detached[0]=='warm' else [x for x in (detached[1],detached[3]) if x is not None]):
   frame,scene=unpack(packet,rom);assert pack(frame,scene)==packet
  # Prove the original receiver copied every scene section before release.
  memory.buf[:size]=b'\0'*size;assert pickle.dumps(detached,protocol=5)==baseline
  checks.append(dict(command=request[0],serial=writer.serial,bytes=size,chunks=writer.last_write_profile['chunk_count'],sha256=hashlib.sha256(actual).hexdigest()))
 assert writer.serial==reader.serial==3
finally:memory.close();memory.unlink();history.close()
out=dict(result='PASS_ACTUAL_SCENE_SHARED_STREAMING_BYTES_IDENTITY_OWNERSHIP',checks=checks,scope='Actual saved paired scene requests through real shared mapping, unchanged detached receiver, original pack/unpack/repack validation including warm/fullpair/retainedolder identity. Same-process descriptor shim, not crossprocess timing or broad gameplay proof.')
Path('work/camera/prototype-runs/streaming-input-actual-scene-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out['result']);print(checks)
