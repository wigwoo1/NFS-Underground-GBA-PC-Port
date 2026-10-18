import struct,json,tracemalloc
from pathlib import Path
from owned_segmented_frame_candidate import SegmentedFrame
from owned_segmented_process_encode_candidate import encode_samples as copied
from owned_segmented_borrowed_tail_encode_candidate import encode_samples as borrowed
from owned_shared_blob import SharedBlobOwner
from owned_shared_payload import write_payload,read_payload,parts
header=struct.pack('<6I2Q',0x3346474e,3,0,1024*1024,0,0,2,3*280896);base=header+b'Z'*(1024*1024);frame=SegmentedFrame(header,base,40);samples={.25:(frame,None,None,None,{}),.75:(frame,None,None,None,{})}
reference=copied(samples);tracemalloc.start();payload=borrowed(samples,borrow_tails=True);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
assert len(payload['tails'])==1 and payload['tails'][0].obj is base and payload['tails'][0].readonly
samples.clear();del frame,base
owner=SharedBlobOwner(4*1024*1024)
try:
 descriptor=write_payload(owner.memory,payload,3,1);decoded=read_payload(descriptor,3,owner.memory);assert decoded==reference
 # Consumer bytes stay independent after the publisher overwrites the mapping.
 write_payload(owner.memory,{'replacement':b'other'},3,2);assert decoded==reference
 try:parts({'tail':memoryview(bytearray(b'mutable'))})
 except ValueError:pass
 else:raise AssertionError('Mutable shared span accepted')
finally:owner.close()
out=dict(result='PASS_BORROWED_IMMUTABLE_TAIL_LIFETIME',borrowed_peak_bytes=peak,tail_bytes=1024*1024,source_samples_cleared_before_write=True,consumer_survives_mapping_reuse=True,mutable_span_rejected=True,scope='Synthetic immutable1MiBtail lifetime and exact shared read; actual source/native4K parity is separate.')
Path('work/camera/prototype-runs/borrowed-tail-owner-20261009.json').write_text(json.dumps(out,indent=2));print(out)
