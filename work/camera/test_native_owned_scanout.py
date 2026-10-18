
from pathlib import Path
import ctypes as C,json,struct,time
p=Path('work/camera');d=C.CDLL(str((p/'native_sprite.dll').resolve()))
d.nf_layer_snapshot_create.restype=C.c_void_p
d.nf_layer_snapshot_add.argtypes=[C.c_void_p,C.c_void_p]
d.nf_layer_snapshot_destroy.argtypes=[C.c_void_p]
d.nfs_native_snapshot_rgb4.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
checks=[]
for closing,scan in [(8757,8758),(8761,8762),(8765,8766),(8768,8769),(8772,8773),(8775,8776),(8779,8780)]:
 rows=(p/f'motion-actual-scanline-assets/{scan}-rows.bin').read_bytes();vram=(p/f'native-closing-vram-assets/{closing}-vram.bin').read_bytes();owner=d.nf_layer_snapshot_create();assert owner
 try:
  for y in range(160):assert d.nf_layer_snapshot_add(owner,rows[y*100480:(y+1)*100480])
  out=(C.c_uint32*38400)(*[0xdeadbeef]*38400);start=time.perf_counter();assert d.nfs_native_snapshot_rgb4(owner,scan,vram,out);elapsed=time.perf_counter()-start
  expected=(p/f'motion-actual-scanline-assets/{scan}-native-rgb.bin').read_bytes();assert bytes(out)==expected
  before=bytes(out);assert not d.nfs_native_snapshot_rgb4(owner,scan+1,vram,out);assert bytes(out)==before
  bad=bytearray(vram);page=0xa000 if struct.unpack_from('<H',rows,8)[0]&16 else 0;bad[page]^=1
  assert not d.nfs_native_snapshot_rgb4(owner,scan,bytes(bad),out);assert bytes(out)==before
  checks.append(dict(scan_refresh=scan,pixels=38400,component_seconds=elapsed))
 finally:d.nf_layer_snapshot_destroy(owner)
report=dict(result='PASS_NATIVE_OWNED_SCANOUT_RGB',checks=checks,pixels=268800,scope='Owned snapshot native C composition with native world/OBJ VRAM. Atomic rejection tested for refresh/page mismatch. Component timings exclude game/GPU; not playable4K or60fps proof.')
(p/'native-owned-scanout-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
