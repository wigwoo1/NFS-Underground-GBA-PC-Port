import os,pickle
os.environ["NFSUG_DESCRIPTOR_RECEIVE_TRACE"]="1"
from multiprocessing.shared_memory import SharedMemory
from owned_progressive_shared_transport_candidate import SharedConnection
from pathlib import Path
import json
class QueueConnection:
 def __init__(self):self.messages=[]
 def send(self,m):self.messages.append(m)
 def recv(self):return self.messages.pop(0)
 def recv_bytes(self):return pickle.dumps(self.recv(),protocol=5)
 def close(self):pass
memory=SharedMemory(create=True,size=1024);q=QueueConnection();writer=SharedConnection(q,memory,True);reader=SharedConnection(q,memory);rejected=0
try:
 packet=(.5,b'private-frame',b'camera');writer.send(('sample',2,0,packet));received=reader.recv();assert received==('sample',2,0,packet)
 profile=reader.last_read_profile['descriptor_receive'];assert profile['begin_ns']<=profile['read_ns']<=profile['decoded_ns']<=reader.last_read_profile['begin_ns'] and profile['wire_bytes']>0
 memory.buf[:memory.size]=b'x'*memory.size;assert received[3]==packet
 for descriptor in [('sample_shared',2,0,1,10),('sample_shared',2,0,3,10),('sample_shared',-1,0,2,10),('sample_shared',2,8,2,10),('sample_shared',2,0,2,0),('sample_shared',2,0,2,1025),('sample_shared',2,0,True,10)]:
  q.send(descriptor)
  try:reader.recv()
  except ValueError:rejected+=1
  else:raise AssertionError('Invalid descriptor accepted')
 try:writer.send(('sample',2,1,(b'x'*2048,)))
 except ValueError:rejected+=1
 else:raise AssertionError('Oversized sample accepted')
 assert not q.messages and writer.serial==1 and reader.serial==1
 writer.send(('sample',2,1,packet));assert reader.recv()==('sample',2,1,packet)
 name=memory.name
finally:memory.close();memory.unlink()
try:SharedMemory(name=name)
except FileNotFoundError:pass
else:raise AssertionError('Publication mapping leaked')
out=dict(result='PASS_PROGRESSIVE_SHARED_DESCRIPTOR_OWNERSHIP',rejected=rejected,private_copy_survives_overwrite=True,fresh_serial_valid=True,mapping_unlinked=True,scope='Bounded transport component, not live timing qualification.')
Path('outputs/nfsug-native-renderer/camera-research/descriptor-receive-component-20261010.json').write_text(json.dumps(out,indent=2));print(out['result'])
