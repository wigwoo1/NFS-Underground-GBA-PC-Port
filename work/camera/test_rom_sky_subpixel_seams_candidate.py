import ctypes as C,json,struct,hashlib
from pathlib import Path
import numpy as np
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791512193343217400.json').read_text());origin=report['sky_capture_records'][0]['asset_origin']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();asset=rom[origin-0x08000000:origin-0x08000000+15376];assert len(asset)==15376
frame=(p/'prototype-runs/profile-scene-1791434844226808400/older.frame.bin').read_bytes();gn=struct.unpack_from('<I',frame,8)[0];pal=np.stack([np.frombuffer(frame,dtype='<u2',count=256,offset=40+gn+y*34944+32896) for y in range(160)])
d=C.CDLL(str((p/'owned-d3d-sky-subpixel-transaction-candidate.dll').resolve()));P=C.c_void_p
for n,a in [('nf_d3d_clear',[P]),('nf_d3d_texture',[C.c_uint,C.c_uint,C.c_uint,P,C.c_size_t]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_sky_pan',[C.c_float]),('nf_d3d_sky_quad',[C.c_uint,C.c_float])]:getattr(d,n).argtypes=a
assert d.nf_d3d_open()==0;buf=C.create_string_buffer(3840*2160*4)
def draw(phase):
 assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0;assert d.nf_d3d_sky_pan(phase)==0;assert d.nf_d3d_read(buf,len(buf))==0
 return np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4).copy()
def plane(offset):
 a=np.zeros((160,240,4),np.uint8);i=np.arange(15136);y=44+i//240;x=i%240
 indices=np.frombuffer(asset[offset:offset+15136],np.uint8);colors=pal[y,indices]
 for k in range(3):
  v=(colors>>(5*k))&31;a[y,x,k]=(v<<3)|(v>>2)
 a[y,x,3]=255
 return a
def upload(offsets):
 for layer,offset in enumerate(offsets):
  a=plane(offset);assert d.nf_d3d_texture(1001+layer,240,160,a.ctypes.data,a.nbytes)==0
rows=[]
try:
 for base in (0,58,238,239):
  upload((base,(base+1)%240));before=draw(1)
  upload(((base+1)%240,(base+2)%240));after=draw(0)
  changed=int(np.count_nonzero(np.any(before!=after,axis=2)))
  rows.append(dict(base=base,changed_pixels=changed,max_channel_difference=int(np.abs(before.astype(np.int16)-after.astype(np.int16)).max())))
finally:assert d.nf_d3d_close()==0
out=dict(result="FAIL_CONTINUITY" if any(r["changed_pixels"] for r in rows) else "PASS_CONTINUITY",rows=rows,scope="Actual ROM4K source-column rollover continuity at equal phase, with same captured scanline palette. Diagnostic finding; no live timing/scanout proof.")
(p/"prototype-runs/rom-sky-subpixel-seams-20261009.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
