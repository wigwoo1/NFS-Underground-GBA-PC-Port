from pathlib import Path
import json
from owned_progressive_frame_codec_candidate import FrameEncoder,FrameDecoder
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns)
e=FrameEncoder(7);d=FrameDecoder(7);wires=[];decoded=[]
for p in ns['packets']:
 wire=e.encode(p[1]);wires.append(wire);frame=d.decode(wire);assert bytes(frame)==bytes(p[1]);decoded.append(frame)
assert e.sent_bytes<e.raw_bytes and len(d.owners)<=2
bad=[('segmented',8,*wires[0][2:]),('segmented',7,1,wires[0][3],wires[0][4],None),wires[0]]
for wire in bad:
 try:d.decode(wire)
 except ValueError:pass
 else:raise AssertionError('Invalid registration accepted')
before=bytes(decoded[0]);d.close();assert d.bytes==0 and not d.owners and bytes(decoded[0])==before
out=dict(result='PASS_PROGRESSIVE_FRAME_REUSE',samples=6,endpoint_owners=len(e.owners),raw_frame_owner_bytes=e.raw_bytes,transferred_frame_owner_bytes=e.sent_bytes,saved_bytes=e.raw_bytes-e.sent_bytes,invalid_wires_rejected=3,delivered_owner_survives_decoder_close=True,scope='Frame-owner payload bytes exclude pickle/protocol/array overhead; not measured bandwidth or live timing.')
Path('outputs/nfsug-native-renderer/camera-research/progressive-frame-codec-20261009.json').write_text(json.dumps(out,indent=2));print(out)
