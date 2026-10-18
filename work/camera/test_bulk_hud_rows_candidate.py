import ctypes as C,struct,json
from pathlib import Path
library=C.CDLL(str(Path('work/camera/layer-snapshot-bulk-hud-candidate.dll').resolve()));P=C.c_void_p
library.nf_layer_snapshot_create.restype=P
library.nf_layer_snapshot_destroy.argtypes=[P]
library.nf_layer_snapshot_add_dirty.argtypes=[P,P,P,P,P,C.c_uint32,C.c_uint]
library.nf_layer_snapshot_read_hud.argtypes=[P,C.c_uint,P]
library.nf_layer_snapshot_read_hud_private_rows.argtypes=[P,C.c_uint,P,C.c_size_t]
library.nf_bulk_test_header_refresh.argtypes=[P,C.c_uint,C.c_uint]
row_bytes=34944;size=160*row_bytes;stats=(C.c_uint64*2)();snapshots=[]
try:
 for bad in (False,True):
  snapshot=library.nf_layer_snapshot_create();assert snapshot;snapshots.append(snapshot)
  vram=C.create_string_buffer(0x18000);palette=C.create_string_buffer(1024);oam=C.create_string_buffer(1024)
  for y in range(160):
   header=C.create_string_buffer(128);struct.pack_into('<II',header,0,42,y);header[10]=bytes([y])
   dirty=0x1ffffff if y==0 else 0
   if y in (60,61):vram[0x10000]=bytes([y]);dirty|=1<<16
   if y==90:palette[0]=b'\x77';dirty|=1<<24
   assert library.nf_layer_snapshot_add_dirty(snapshot,header,vram,palette,oam,dirty,0)==1
  if bad:assert library.nf_bulk_test_header_refresh(snapshot,159,43)==1
  out=C.create_string_buffer(b'X'*size)
  result=library.nf_layer_snapshot_read_hud_private_rows(snapshot,42,out,size)
  if bad:assert result==0 and out.raw==b'X'*size+b'\0';continue
  assert result==1
  reference=C.create_string_buffer(size)
  for y in range(160):assert library.nf_layer_snapshot_read_hud(snapshot,y,C.byref(reference,y*row_bytes))==1
  assert out.raw==reference.raw+b'\0'
  for refresh,capacity in ((43,size),(42,size-1)):
   sentinel=C.create_string_buffer(b'X'*size);assert library.nf_layer_snapshot_read_hud_private_rows(snapshot,refresh,sentinel,capacity)==0 and sentinel.raw==b'X'*size+b'\0'
 library.nf_layer_bulk_hud_stats(stats);assert stats[0]>150 and stats[1]>=4
 out=dict(result='PASS_BULK_HUD_ALL_ROWS_PRIVATE_PARITY',same_page_rows=stats[0],rebuilt_rows=stats[1],late_bad_header_rejected_before_output=True)
 Path('work/camera/prototype-runs/bulk-hud-component-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 for snapshot in snapshots:library.nf_layer_snapshot_destroy(snapshot)
