"""Projection-only private RAM clone lifetime and immutable source checks."""
import ctypes as C,struct,json
from pathlib import Path
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
d.nf_visibility_assets_create.argtypes=[P,Z];d.nf_visibility_assets_create.restype=P
d.nf_visibility_snapshot_create_prepared.argtypes=[P,P,Z,U,U];d.nf_visibility_snapshot_create_prepared.restype=P
d.nf_visibility_snapshot_clone_focal.argtypes=[P,U];d.nf_visibility_snapshot_clone_focal.restype=P
d.nf_visibility_snapshot_read.argtypes=[P,U,P,Z];d.nf_visibility_snapshot_destroy.argtypes=[P];d.nf_visibility_assets_release.argtypes=[P]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
assets=d.nf_visibility_assets_create(rom,len(rom));assert assets
checks=0
try:
 for address in [0x02000200,0x03000200]:
  ram=bytearray(0x48000);struct.pack_into('<I',ram,80,address);struct.pack_into('<I',ram,84,0x02000100)
  offset=address-0x02000000 if address<0x03000000 else 0x40000+address-0x03000000
  struct.pack_into('<I',ram,offset+28,136);buffer=C.create_string_buffer(bytes(ram))
  source=d.nf_visibility_snapshot_create_prepared(assets,buffer,len(ram),0x02000000,0);assert source
  clones=[]
  try:
   for focal in [76,82,88,136]:
    clone=d.nf_visibility_snapshot_clone_focal(source,focal);assert clone;clones.append(clone)
    actual=C.create_string_buffer(0x40000);assert d.nf_visibility_snapshot_read(source,0x02000000,actual,0x40000);assert actual.raw==ram[:0x40000]
    data=C.create_string_buffer(32);assert d.nf_visibility_snapshot_read(clone,address,data,32);expected=bytearray(ram[offset:offset+32]);struct.pack_into('<I',expected,28,focal);assert data.raw==expected
    checks+=1
   for focal in [0,32768,0xffffffff]:assert not d.nf_visibility_snapshot_clone_focal(source,focal)
  finally:d.nf_visibility_snapshot_destroy(source)
  for clone in clones:
   data=C.create_string_buffer(32);assert d.nf_visibility_snapshot_read(clone,address,data,32);d.nf_visibility_snapshot_destroy(clone)
finally:d.nf_visibility_assets_release(assets)
assert not d.nf_visibility_snapshot_clone_focal(None,82)
report=dict(result='PASS',projection_clones=checks,scope='Synthetic EWRAM/IWRAM projection cloning modifies only focal word, leaves source unchanged and survives source destruction. Not integrated with sampled planner or original zoom GPU yet.')
(p/'owned-focal-clone-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
