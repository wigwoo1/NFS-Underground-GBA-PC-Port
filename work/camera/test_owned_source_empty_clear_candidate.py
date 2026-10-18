import ctypes as C,json,hashlib
from pathlib import Path
from owned_source_d3d_empty_consumer_candidate import OwnedD3DConsumer
p=Path(__file__).parent;s=C.CDLL(str((p/'owned-gpu-source-empty-candidate.dll').resolve()));s.nf_source_packets_begin.argtypes=[C.c_uint64]*3;s.nf_source_packets_publish.argtypes=[C.c_void_p]
assert s.nf_source_packets_begin(7,9,0)==0
publication=(C.c_uint64*7)();assert s.nf_source_packets_publish(publication)==0;assert list(publication)==[7,9,0,0,0,0,0];assert s.nf_source_packets_publish(publication)==1
consumer=OwnedD3DConsumer()
try:
 image=consumer.render(s);assert (image==[9,13,20]).all();digest=hashlib.sha256(image.tobytes()).hexdigest()
finally:consumer.close();assert s.nf_source_packets_close()==0
assert s.nf_source_backdrop_count()==-1
r=dict(result='PASS_EMPTY_SOURCE_PUBLICATION_D3D_CLEAR',publication=list(publication),rgb_sha256=digest,pixels=8294400,scope='Synthetic clear-only source frame, no source GL drawing or readback. Empty publication and D3D consumption verified; real menu/transition capture remains required.')
(p/'prototype-runs/source-empty-clear-component.json').write_text(json.dumps(r,indent=2));print(r)
