from pathlib import Path
import json
from owned_progressive_frame_codec_candidate import FrameEncoder,FrameDecoder
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns)
owners=[]
for packet in ns['packets']:
 if not any(x is packet[1].base for x in owners):owners.append(packet[1].base)
owners=tuple(owners);e=FrameEncoder(7,owners);d=FrameDecoder(7,owners=owners);frames=[]
for packet in ns['packets']:
 wire=e.encode(packet[1]);assert wire[-1] is None
 f=d.decode(wire);assert bytes(f)==bytes(packet[1]) and f.base is owners[wire[2]];frames.append(f)
assert e.sent_bytes==sum(len(p[1].prefix) for p in ns['packets'])
before=bytes(frames[0]);d.close();assert bytes(frames[0])==before
for make in (lambda:FrameDecoder(7,budget=1,owners=owners),lambda:FrameEncoder(7,(bytearray(40),))):
 try:make()
 except ValueError:pass
 else:raise AssertionError('Invalid seeded ownership accepted')
out=dict(result='PASS_SEEDED_PROGRESSIVE_ENDPOINT_REFERENCE',samples=len(frames),endpoint_owners=len(owners),frame_owner_bytes_without_reuse=e.raw_bytes,transferred_frame_owner_bytes=e.sent_bytes,saved_frame_owner_bytes=e.raw_bytes-e.sent_bytes,no_endpoint_payloads=True,private_owner_survives_close=True,scope='Exact input endpoint reuse within an explicitly seeded request; includes all complete frame bytes, excludes array/protocol overhead. No live speed proof.')
Path('outputs/nfsug-native-renderer/camera-research/progressive-seeded-frame-20261009.json').write_text(json.dumps(out,indent=2));print(out)
