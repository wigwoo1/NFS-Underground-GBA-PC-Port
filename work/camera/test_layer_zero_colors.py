from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'zero-layer-snapshot.dll').resolve()))
d.nf_layer_snapshot_create.restype=C.c_void_p
d.nf_layer_snapshot_add.argtypes=[C.c_void_p,C.c_void_p]
d.nf_layer_snapshot_zero_colors.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p]
d.nf_layer_snapshot_destroy.argtypes=[C.c_void_p]
s=d.nf_layer_snapshot_create();out=(C.c_uint16*160)(*([0xa5a5]*160));guards=0
try:
 for y in range(160):
  row=bytearray(100480);struct.pack_into('<2I',row,0,77,y);struct.pack_into('<H',row,128+0x18000,(y*137)&65535)
  assert d.nf_layer_snapshot_add(s,bytes(row))
  row[:]=bytes(len(row)) # caller mutation must not alter retained palette
  if y<159:
   assert not d.nf_layer_snapshot_zero_colors(s,77,out) and list(out)==[0xa5a5]*160;guards+=1
 assert not d.nf_layer_snapshot_zero_colors(s,78,out) and list(out)==[0xa5a5]*160;guards+=1
 assert d.nf_layer_snapshot_zero_colors(s,77,out) and list(out)==[(y*137)&65535 for y in range(160)]
finally:d.nf_layer_snapshot_destroy(s)
report=dict(result='PASS',owned_rows=160,atomic_rejections=guards,scope='Exact refresh-owned raw BGR555 scanline colors, no current-palette reads; native rendering integration remains pending.')
(p/'layer-zero-colors-tests.json').write_text(json.dumps(report,indent=2));print(report)
