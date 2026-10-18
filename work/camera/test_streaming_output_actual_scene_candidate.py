import sys,json,struct,types
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'savedscene','exec'))
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,(0.25,0.5,0.75),trace=False)
actual_payloads=[]
for alpha in (0.25,0.5,0.75):
 frame,camera,models,bounds,detail=cached.sample(alpha);packed=cached.source_masks[alpha]
 actual_payloads.append((alpha,frame,bytes(camera),bytes(models),bytes(bounds),bytes(packed[0]),bytes(packed[1]),packed[2],json.dumps(detail,sort_keys=True).encode(),json.dumps(packed[3],sort_keys=True).encode(),cached.source_cameras))
import pickle,json,time,statistics,gc
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
from owned_progressive_shared_transport_candidate import SharedConnection
from owned_streaming_output_write_candidate import send
class Connection:
 def __init__(self):self.message=None
 def send(self,message):self.message=message
 def recv(self):return self.message
memory=SharedMemory(create=True,size=16*1024*1024)
try:
 conn=Connection();writer=SharedConnection(conn,memory,True);reader=SharedConnection(conn,memory)
 payloads=actual_payloads
 results=[]
 for index,payload in enumerate(payloads):
  message=('sample',2,index,payload);send(writer,message)
  expected=pickle.dumps(payload,protocol=5)
  assert bytes(memory.buf[:len(expected)])==expected
  detached=reader.recv();assert detached==message
  memory.buf[:len(expected)]=b'x'*len(expected)
  assert detached==message
  results.append(dict(bytes=len(expected),chunks=writer.last_write_profile['chunk_count']))
 before=writer.serial;conn.message=None
 try:send(writer,('sample',2,3,b'x'*memory.size))
 except ValueError:pass
 else:raise AssertionError('Unbounded output accepted')
 assert writer.serial==before and conn.message is None
 send(writer,('terminal',2,'complete'));assert conn.message==('terminal',2,'complete')
 baseline=SharedConnection.send;samples={'baseline':[],'candidate':[]};payload=payloads[1]
 enabled=gc.isenabled();gc.disable()
 try:
  for iteration in range(160):
   order=[('baseline',baseline),('candidate',send)]
   if iteration%2:order.reverse()
   for label,fn in order:
    begin=time.perf_counter_ns();fn(writer,('sample',2,0,payload));samples[label].append((time.perf_counter_ns()-begin)/1e6)
 finally:
  if enabled:gc.enable()
 medians={key:statistics.median(value) for key,value in samples.items()}
 out=dict(result='PASS_STREAMING_OUTPUT_PROTOCOL_AND_BOUNDS',payloads=results,median_ms=medians,ratio=medians['candidate']/medians['baseline'],samples_ms=samples,scope='Actual saved-scene output packets (three fractional phases), exact protocol5 bytes, detached unchanged receiver, overflow leaves serial/descriptor unpublished, control pass-through; same-input alternating send benchmark. No actual scene pixel or live timing claim.')
 Path('work/camera/prototype-runs/streaming-output-actual-scene-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],medians,out['ratio'])
finally:memory.close();memory.unlink();cached.close();prepared.close();history.close()

