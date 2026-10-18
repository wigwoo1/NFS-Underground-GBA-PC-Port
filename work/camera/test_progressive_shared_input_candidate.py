from multiprocessing.shared_memory import SharedMemory
from owned_progressive_shared_transport_candidate import SharedInputConnection
from pathlib import Path
import json
class QueueConnection:
 def __init__(self):self.messages=[]
 def send(self,m):self.messages.append(m)
 def recv(self):return self.messages.pop(0)
 def close(self):pass
memory=SharedMemory(create=True,size=1024);q=QueueConnection();writer=SharedInputConnection(q,memory,True);reader=SharedInputConnection(q,memory);rejected=0
try:
 request=(3,(b'older',),('identity',),(b'newer',),(.5,),True)
 writer.send(request);copied=reader.recv();assert copied==request
 memory.buf[:memory.size]=b'x'*memory.size;assert copied==request
 for descriptor in [('request_shared',1,10),('request_shared',3,10),('request_shared',True,10),('request_shared',2,0),('request_shared',2,1025),('request_shared',2)]:
  q.send(descriptor)
  try:reader.recv()
  except ValueError:rejected+=1
  else:raise AssertionError('Invalid descriptor accepted')
 try:writer.send((3,b'x'*2048))
 except ValueError:rejected+=1
 else:raise AssertionError('Oversized input accepted')
 assert writer.serial==reader.serial==1 and not q.messages
 warm=('warm',3,(b'frame',));writer.send(warm);assert reader.recv()==warm
 writer.send(('ack',3,0));assert reader.recv()==('ack',3,0)
 writer.send(None);assert reader.recv() is None
 name=memory.name
finally:memory.close();memory.unlink()
try:SharedMemory(name=name)
except FileNotFoundError:pass
else:raise AssertionError('Input mapping leaked')
out=dict(result='PASS_SHARED_INPUT_PRIVATE_OWNERSHIP',invalid_descriptors_and_budget_rejected=rejected,private_copy_survives_overwrite=True,warm_roundtrip=True,control_messages_preserved=True,mapping_unlinked=True,scope='Input transport component; full native tests separate, live timing unverified.')
Path('outputs/nfsug-native-renderer/camera-research/progressive-shared-input-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
