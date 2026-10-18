import pickle,json,time,statistics,gc
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
from owned_progressive_shared_transport_candidate import SharedConnection
from owned_streaming_output_write_candidate import send
class Connection:
 def __init__(self):self.message=None
 def send(self,message):self.message=message
 def recv(self):return self.message
memory=SharedMemory(create=True,size=4*1024*1024)
try:
 conn=Connection();writer=SharedConnection(conn,memory,True);reader=SharedConnection(conn,memory)
 payloads=[(0.25,b'f'*size,b'camera',b'models',b'bounds',b'offsets',b'mask',17,b'{}',b'{}',((1.0,)*12,)*2) for size in (64,900000,3000000)]
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
 out=dict(result='PASS_STREAMING_OUTPUT_PROTOCOL_AND_BOUNDS',payloads=results,median_ms=medians,ratio=medians['candidate']/medians['baseline'],samples_ms=samples,scope='Representative output payloads, exact protocol5 bytes, detached unchanged receiver, overflow leaves serial/descriptor unpublished, control pass-through; same-input alternating send benchmark. No actual scene pixel or live timing claim.')
 Path('work/camera/prototype-runs/streaming-output-component-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],medians,out['ratio'])
finally:memory.close();memory.unlink()
