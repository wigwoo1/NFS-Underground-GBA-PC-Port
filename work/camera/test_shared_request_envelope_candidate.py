import json
from pathlib import Path
from owned_shared_blob import SharedBlobOwner
from owned_shared_payload import write_payload
from owned_shared_request_service_candidate import ParentConnection,ChildConnection
class Channel:
 def __init__(self,value=None):self.value=value;self.sent=[];self.closed=False
 def recv(self):return self.value
 def send(self,value):self.sent.append(value)
 def close(self):self.closed=True
 def poll(self,timeout):return False
owner=SharedBlobOwner(4096);checks=[]
try:
 request=(3,None,(1,2), (b'frame',b'graph',b'supplement',None,None),(.25,))
 descriptor=write_payload(owner.memory,request,3,1);channel=Channel(('request_shared',descriptor));child=ChildConnection(channel,owner.memory.name)
 try:
  received=child.recv();assert received==request and channel.sent==[('request_ack',descriptor)]
  write_payload(owner.memory,{'changed':b'other'},3,2);assert received==request;checks.append('owned_request_survives_mapping_reuse')
 finally:child.close()
 for label,payload,change in [('bad_serial',request,lambda d:(d[0],d[1],2,d[3])),('bad_owner',request,lambda d:('wrong',*d[1:])),('generation_mismatch',(4,*request[1:]),lambda d:d),('bad_envelope',{'bad':True},lambda d:d)]:
  descriptor=write_payload(owner.memory,payload,3,1);channel=Channel(('request_shared',change(descriptor)));child=ChildConnection(channel,owner.memory.name)
  try:
   try:child.recv()
   except ValueError:assert channel.sent[0][0]=='request_error';checks.append(label)
   else:raise AssertionError(label)
  finally:child.close()
 parent=ParentConnection(Channel(),owner)
 try:parent.send(request)
 except RuntimeError:assert parent.failed and parent.acknowledged==0;checks.append('missing_ack_fails_channel')
 else:raise AssertionError('Missing ack accepted')
 try:parent.send(request)
 except RuntimeError:checks.append('failed_channel_rejects_reuse')
 else:raise AssertionError('Failed request mapping reused')
finally:owner.close()
out=dict(result='PASS_SHARED_REQUEST_ENVELOPE_AND_ACK',checks=checks,scope='Actual mapping with local deterministic control channel. Spawned/native4K and live lifecycle verified separately; no blocked child timeout qualification.')
Path('work/camera/prototype-runs/shared-request-envelope-20261009.json').write_text(json.dumps(out,indent=2));print(out)
