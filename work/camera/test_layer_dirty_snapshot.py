"""Exact dirty-mask ownership and rejection of a falsely clean page."""
from pathlib import Path
import ctypes as C,struct,json,random
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'))
d.nf_layer_snapshot_create.restype=C.c_void_p
d.nf_layer_snapshot_destroy.argtypes=[C.c_void_p]
d.nf_layer_snapshot_read.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
add=d.nf_layer_snapshot_add_dirty;add.argtypes=[C.c_void_p]*5+[C.c_uint32,C.c_uint]
rng=random.Random(4728);snap=d.nf_layer_snapshot_create();expected=[]
try:
 memory=bytearray(rng.randbytes(100352))
 for row in range(160):
  page=row%25;offset=page*4096 if page<24 else 0x18000+(row%2048)
  memory[offset]^=1
  raw=struct.pack('<2I',888,row)+rng.randbytes(120)+memory
  buf=C.create_string_buffer(raw,len(raw))
  assert add(snap,buf,C.byref(buf,128),C.byref(buf,128+0x18000),C.byref(buf,128+0x18400),1<<page,0)
  expected.append(bytes(raw));C.memset(buf,0,len(raw))
 out=C.create_string_buffer(100480)
 for row,raw in enumerate(expected):assert d.nf_layer_snapshot_read(snap,row,out) and out.raw==raw
finally:d.nf_layer_snapshot_destroy(snap)
snap=d.nf_layer_snapshot_create()
try:
 buf=C.create_string_buffer(100480);struct.pack_into('<2I',buf,0,999,0)
 args=[snap,buf,C.byref(buf,128),C.byref(buf,128+0x18000),C.byref(buf,128+0x18400)]
 assert add(*args,0,1) # first row always imports every page
 struct.pack_into('<I',buf,4,1);buf[128+7*4096]=b'X'
 assert not add(*args,0,1) # missed notification must fail
 assert add(*args,1<<7,1)
finally:d.nf_layer_snapshot_destroy(snap)
report=dict(result='PASS',exact_rows=160,all_25_pages_changed=True,caller_mutation_isolated=True,false_clean_rejected=True,corrected_dirty_retry=True,scope='Snapshot component: exact full rows, first-row import and missed dirty notification rejection. Live callback coverage and pacing require full-route tests.')
(p/'layer-dirty-snapshot-tests.json').write_text(json.dumps(report,indent=2));print(report)
