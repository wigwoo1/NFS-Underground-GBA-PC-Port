import pickle,json
from types import SimpleNamespace
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
import owned_progressive_shared_transport_candidate as transport
original=transport.SharedInputConnection.recv
import owned_direct_shared_input_decode_install_candidate as candidate
def result(fn,message,payload,serial=0):
 memory=SharedMemory(create=True,size=4096)
 try:
  memory.buf[:len(payload)]=payload
  channel=SimpleNamespace(recv=lambda:message)
  owner=transport.SharedInputConnection(channel,memory);owner.serial=serial
  try:return 'ok',fn(owner),owner.serial
  except Exception as e:return type(e).__name__,str(e),owner.serial
 finally:memory.close();memory.unlink()
payload=pickle.dumps((1,(b'private',)),protocol=5);cases=[]
for message in [('request_shared',1,len(payload)),('request_shared',1),('request_shared',2,len(payload)),('request_shared',True,len(payload)),('request_shared',1,0),('request_shared',1,4097),('request_shared',1,True),None]:cases.append((message,payload))
for body in [(),('bad',),[1,b'x']]:
 raw=pickle.dumps(body,protocol=5);cases.append((('request_shared',1,len(raw)),raw))
for message,raw in cases:assert result(original,message,raw)==result(transport.SharedInputConnection.recv,message,raw)
transport.SharedInputConnection.recv=original
out=dict(result='PASS_DIRECT_SHARED_DECODE_PROTOCOL_GUARDS',cases=len(cases),scope='Original/candidate descriptor serial/extent/type/command error parity and successful decoded tuple; every SharedMemory closes/unlinks after success/error, no outstanding view exports.')
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/direct-shared-input-decode-20261010');(folder/'guards.json').write_text(json.dumps(out,indent=2));print(out['result'])
