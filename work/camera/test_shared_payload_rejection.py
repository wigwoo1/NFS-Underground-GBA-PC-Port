import struct,pickle,json
from pathlib import Path
from owned_shared_blob import SharedBlobOwner,_HEADER
from owned_shared_payload import write_payload,read_payload,ByteReference
owner=SharedBlobOwner(4096);checks=0
try:
 def reject(fn):
  global checks
  try:fn()
  except ValueError:checks+=1;return
  raise AssertionError('Invalid shared payload accepted')
 def reset():return write_payload(owner.memory,{'bytes':b'valid'},3,1)
 d=reset();assert read_payload(d,3)=={'bytes':b'valid'}
 reject(lambda:read_payload(d,4));reject(lambda:read_payload((d[0],3,2,d[3]),3))
 for meta,count in ((2**20+1,1),(1,513),(4096,1),(1,512)):
  d=reset();struct.pack_into('<2I',owner.memory.buf,_HEADER.size,meta,count);reject(lambda:read_payload(d,3))
 d=reset();struct.pack_into('<I',owner.memory.buf,_HEADER.size+8,1000);reject(lambda:read_payload(d,3))
 metadata=pickle.dumps(ByteReference(99),protocol=5);body=struct.pack('<2I',len(metadata),0)+metadata;owner.memory.buf[_HEADER.size:_HEADER.size+len(body)]=body;header=list(_HEADER.unpack_from(owner.memory.buf));header[3]=len(body);_HEADER.pack_into(owner.memory.buf,0,*header);reject(lambda:read_payload((owner.memory.name,3,1,len(body)),3))
 reject(lambda:write_payload(owner.memory,{'bytes':b'a'*4097},3,2));reject(lambda:write_payload(owner.memory,{'bad':object()},3,2))
 d=reset();assert read_payload(d,3)=={'bytes':b'valid'}
finally:owner.close()
out=dict(result='PASS',rejections=checks,valid_recovery=True,scope='Shared payload identity/directory/length/reference/budget rejection; trusted child metadata only')
Path('work/camera/shared-payload-rejection-tests.json').write_text(json.dumps(out,indent=2));print(out)
