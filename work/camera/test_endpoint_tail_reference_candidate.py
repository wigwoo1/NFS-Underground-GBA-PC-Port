import struct,json
from pathlib import Path
from owned_endpoint_tail_reference_candidate import encode_samples,resolve_frame,TAG
from owned_segmented_frame_candidate import SegmentedFrame
from owned_shared_blob import SharedBlobOwner
from owned_shared_payload import write_payload,read_payload
header=struct.pack('<6I2Q',0x3346474e,3,0,1024*1024,0,0,2,3*280896);endpoint=header+b'Z'*(1024*1024);endpoints=(endpoint,endpoint);frame=SegmentedFrame(header,endpoint,40);samples={.25:(frame,None,None,None,{})}
encoded=encode_samples(samples,endpoints);assert encoded['referenced_tail_bytes']==1024*1024 and encoded['transferred_bytes']==40
owner=SharedBlobOwner(4*1024*1024);checks=0
try:
 descriptor=write_payload(owner.memory,encoded,1,1);payload=read_payload(descriptor,1,owner.memory);assert descriptor[3]<2048
 resolved=resolve_frame(payload['samples'][0][1][0],payload['tails'][0],endpoints);assert resolved.base is endpoint and bytes(resolved)==bytes(frame);checks+=1
 for bad in [(TAG,-1,header,1024*1024),(TAG,True,header,1024*1024),(TAG,0,b'bad',1024*1024),(TAG,0,header,2),(TAG,0,header[:-1]+b'X',1024*1024),('bad',0,header,1024*1024)]:
  try:resolve_frame(header,bad,endpoints)
  except ValueError:checks+=1
  else:raise AssertionError('Invalid endpoint reference accepted')
 # A byte-identical separately owned frame must fall back, never assert endpoint identity.
 independent=bytes(bytearray(endpoint));other=SegmentedFrame(header,independent,40)
 fallback=encode_samples({.25:(other,None,None,None,{})},endpoints);assert fallback['referenced_tail_bytes']==0 and isinstance(fallback['tails'][0],memoryview);checks+=1
finally:owner.close()
out=dict(result='PASS_OWNED_ENDPOINT_TAIL_REFERENCE',checks=checks,logical_tail_bytes=1024*1024,shared_payload_bytes=descriptor[3],scope='Synthetic owned1MiBtail transfer/reference rejection/copy fallback; captured/native integration still required.')
Path('work/camera/prototype-runs/endpoint-tail-reference-20261009.json').write_text(json.dumps(out,indent=2));print(out)
