import struct,json
from pathlib import Path
from owned_endpoint_tail_process_service_candidate import endpoint_frame
from owned_segmented_frame_candidate import SegmentedFrame
prefix=struct.pack('<6I2Q',0x3346474e,3,0,16,0,0,2,3*280896)
endpoint=struct.pack('<6I2Q',0x3346474e,3,4,16,0,0,2,3*280896)+b'geom'+b'A'*16
other=struct.pack('<6I2Q',0x3346474e,4,0,16,0,0,2,4*280896)+b'B'*16
owners={'endpoints':(endpoint,other)};a=endpoint_frame(prefix,b'A'*16,0,owners);b=endpoint_frame(prefix,b'A'*16,0,owners)
assert a.base is endpoint and b.base is endpoint and a.tail_offset==44
mismatch=endpoint_frame(prefix,b'C'*16,1,owners);assert mismatch.base is not endpoint and bytes(mismatch)==prefix+b'C'*16
wrong_identity=endpoint_frame(prefix,b'B'*16,2,owners);assert wrong_identity.base is not other and bytes(wrong_identity)==prefix+b'B'*16
out=dict(result='PASS_EXACT_ENDPOINT_TAIL_OWNER',same_owner_reused=True,wrong_bytes_not_reused=True,wrong_refresh_not_reused=True,scope='Synthetic endpoint identity/exacttail/fallback ownership; source/native4K actual capture tests separate.')
Path('work/camera/prototype-runs/endpoint-tail-owner-20261009.json').write_text(json.dumps(out,indent=2));print(out)
