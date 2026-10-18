from pathlib import Path
import ctypes as C,random,struct,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'layer-snapshot-padding-candidate.dll'));d.nf_layer_snapshot_create.restype=C.c_void_p;d.nf_layer_snapshot_destroy.argtypes=[C.c_void_p];d.nf_layer_snapshot_add.argtypes=[C.c_void_p,C.c_void_p];d.nf_layer_snapshot_read.argtypes=[C.c_void_p,C.c_uint,C.c_void_p];d.nf_layer_snapshot_bytes.argtypes=[C.c_void_p];d.nf_layer_snapshot_bytes.restype=C.c_size_t;d.nf_layer_snapshot_pages.argtypes=[C.c_void_p];d.nf_layer_snapshot_reset.argtypes=[C.c_void_p];parts=d.nf_layer_snapshot_add_parts;parts.argtypes=[C.c_void_p]*5
rng=random.Random(679);reports=[]
for kind in ('constant','sparse','random'):
 s=d.nf_layer_snapshot_create();assert s;rows=[];memory=bytearray(rng.randbytes(100352));out=C.create_string_buffer(b'Q'*100480,100480)
 try:
  assert not d.nf_layer_snapshot_read(s,0,out) and out.raw==b'Q'*100480
  for y in range(160):
   if kind=='random':memory[:]=rng.randbytes(len(memory))
   if kind=='sparse':memory[(y*761)%len(memory)]^=1
   b=struct.pack('<2I',999,y)+rng.randbytes(120)+memory;buffer=C.create_string_buffer(b,len(b));assert parts(s,buffer,C.byref(buffer,128),C.byref(buffer,128+0x18000),C.byref(buffer,128+0x18000+1024));rows.append(bytes(b));C.memset(buffer,0,len(b))
  for y in range(160):assert d.nf_layer_snapshot_read(s,y,out) and out.raw==rows[y]
  assert not d.nf_layer_snapshot_add(s,rows[0]);saved=out.raw;assert not d.nf_layer_snapshot_read(s,160,out) and out.raw==saved
  reports.append(dict(kind=kind,rows=160,retained_bytes=d.nf_layer_snapshot_bytes(s),pages=d.nf_layer_snapshot_pages(s)))
  capacity_bytes=d.nf_layer_snapshot_bytes(s);saved=out.raw;assert d.nf_layer_snapshot_reset(s)
  assert d.nf_layer_snapshot_pages(s)==0 and d.nf_layer_snapshot_bytes(s)==capacity_bytes
  assert not d.nf_layer_snapshot_read(s,0,out) and out.raw==saved
  new_memory=rng.randbytes(100352);replacement=[]
  for y in range(160):
   b=struct.pack('<2I',1000,y)+rng.randbytes(120)+new_memory;assert d.nf_layer_snapshot_add(s,b);replacement.append(b)
   if y<159:assert not d.nf_layer_snapshot_read(s,0,out) and out.raw==saved
  for y,b in enumerate(replacement):assert d.nf_layer_snapshot_read(s,y,out) and out.raw==b
  assert d.nf_layer_snapshot_bytes(s)==capacity_bytes
  reports[-1].update(reset_rows_exact=160,reset_capacity_reused=True,reset_old_rows_unavailable=True)
 finally:d.nf_layer_snapshot_destroy(s)
r=dict(result='PASS',cases=reports,scope='Exact immutable page-deduplicated reconstruction, caller mutation isolation, incomplete/invalid/full rejection');(p/'layer-padding-candidate-tests.json').write_text(json.dumps(r,indent=2));print(r)
