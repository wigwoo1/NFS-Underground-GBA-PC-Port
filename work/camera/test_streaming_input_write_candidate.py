"""Byte-identical bounded streaming input and original detached receiver guards."""
import pickle,json
from pathlib import Path
from owned_progressive_shared_transport_candidate import SharedInputConnection
from owned_streaming_input_write_candidate import send
class Memory:
 def __init__(self,n):self.buf=bytearray(n);self.size=n
class Connection:
 def __init__(self):self.items=[]
 def send(self,x):self.items.append(x)
 def recv(self):return self.items.pop(0)
checks=[]
for n in [0,1,65535,65536,8384894,14891603]:
 data=bytes((i%251 for i in range(n)));message=(2,('scene',data),('repeated',data),[b'camera',42,3.25]);expected=pickle.dumps(message,protocol=5)
 memory=Memory(len(expected));pipe=Connection();writer=SharedInputConnection(pipe,memory,True);reader=SharedInputConnection(pipe,memory)
 send(writer,message);assert bytes(memory.buf)==expected and writer.serial==1
 detached=reader.recv();assert detached==message and reader.serial==1
 memory.buf[:]=b'\0'*memory.size;assert detached==message
 checks.append(dict(source_bytes=n,serialized_bytes=len(expected),chunks=writer.last_write_profile['chunk_count']))
 memory=Memory(len(expected)-1);pipe=Connection();writer=SharedInputConnection(pipe,memory,True)
 try:send(writer,message)
 except ValueError:pass
 else:raise AssertionError('Oversize accepted')
 assert writer.serial==0 and pipe.items==[]
# Nonshared controls unchanged; stale serial rejects before exposing a request.
 memory=Memory(len(expected));pipe=Connection();writer=SharedInputConnection(pipe,memory,True);send(writer,('cancel',2));assert pipe.items==[('cancel',2)] and writer.serial==0
 pipe.items=[('request_shared',2,1)];reader=SharedInputConnection(pipe,memory)
 try:reader.recv()
 except ValueError:pass
 else:raise AssertionError('Stale serial accepted')
out=dict(result='PASS_STREAMING_INPUT_EXACT_BYTES_BOUNDS_OWNERSHIP',checks=checks,scope='Protocol5 exact bytes against dumps across size/frame boundaries and14.9MB representative immutable payload; original receiver detach, oversize publication rejection and stale serial. Not actual live scene or timing qualification.')
Path('work/camera/prototype-runs/streaming-input-write-tests-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
