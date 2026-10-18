from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');d=C.CDLL(str((p/'native_sprite.dll').resolve()));d.nfs_sprite_local.argtypes=[C.c_uint,C.c_uint,C.c_int,C.c_int]+[C.c_uint]*4+[C.c_void_p,C.c_void_p];d.nfs_sprite_sample4.argtypes=[C.c_void_p,C.c_size_t]+[C.c_uint]*6+[C.c_void_p]
oracle=C.CDLL(str((p/'sprite_original_oracle.dll').resolve())).nfs_original_sprite_plane;oracle.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
combined_oracle=C.CDLL(str((p/'sprite_original_oracle.dll').resolve())).nfs_original_sprite_combined;combined_oracle.argtypes=oracle.argtypes
d.nfs_sprite_merge.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
from scene_batches import records
frames={e['frame']:e for e in records(p/'motion-original-video-state-world.bin') if e['pc']==0x04000000}
d.nfs_scene_rgb4.argtypes=[C.c_void_p]*7
d.nfs_sprite_oam4.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
checks=[];sprite_cases=0
for scene in json.loads((p/'motion-visible-sprite-modes.json').read_text())['scenes']:
 merged=(C.c_uint16*38400)(*[65535]*38400);order=(C.c_uint16*38400)(*[65535]*38400)
 refresh=scene['refresh'];native_vram=(p/f'native-closing-vram-assets/{refresh}-vram.bin').read_bytes();obj=native_vram[0x14000:0x18000];oam=(p/f'motion-complete-display-assets/{refresh}-oam.bin').read_bytes();samples=outside=opaque=0
 for sprite in scene['visible_bounds_entries']:
  idx=sprite['index'];a,b,c=struct.unpack_from('<3H',oam,idx*8);mat=(C.c_int16*4)(*[struct.unpack_from('<h',oam,sprite['matrix']*32+6+i*8)[0] for i in range(4)])
  original=(C.c_uint16*38400)();assert oracle(obj,oam,idx,0x1f44,original);native=[65535]*38400
  bw=sprite['width']*(2 if sprite['affine'] and sprite['double_size'] else 1);bh=sprite['height']*(2 if sprite['affine'] and sprite['double_size'] else 1)
  for y in range(bh):
   for x in range(bw):
    if not (0<=x+sprite['x']<240 and 0<=y+sprite['y']<160):continue
    xy=(C.c_int*2)();status=d.nfs_sprite_local(sprite['width'],sprite['height'],x,y,sprite['affine'],sprite['double_size'] if sprite['affine'] else 0,bool(b&4096),bool(b&8192),mat,xy)
    if status==2:outside+=1;continue
    assert status==1;out=(C.c_uint32*3)();assert d.nfs_sprite_sample4(obj,len(obj),sprite['width'],sprite['tile'],1,xy[0],xy[1],sprite['palette_bank'],out)
    assert 0x06014000<=out[0]<0x06018000 and out[1]<16 and out[2]<256
    samples+=1;opaque+=out[1]!=0
    if out[1]:native[(y+sprite['y'])*240+x+sprite['x']]=256+out[2]
  diffs=[i for i in range(38400) if native[i]!=original[i]]
  assert not diffs,(refresh,idx,len(diffs),diffs[:5]);sprite_cases+=1
  plane=(C.c_uint16*38400)(*native);assert d.nfs_sprite_merge(plane,sprite['priority'],idx,merged,order)
 combined=(C.c_uint16*38400)();assert combined_oracle(obj,oam,0,0x1f44,combined);diffs=[i for i in range(38400) if merged[i]!=combined[i]];assert not diffs,(refresh,'combined',len(diffs),diffs[:5])
 scan_refresh={8757:8758,8761:8762,8765:8766,8768:8769,8772:8773,8775:8776,8779:8780}[refresh]
 native_merged=(C.c_uint16*38400)();native_order=(C.c_uint16*38400)();assert d.nfs_sprite_oam4(obj,oam,0x1f44,native_merged,native_order)
 assert bytes(native_merged)==bytes(merged) and bytes(native_order)==bytes(order),(refresh,'native OAM decode')
 merged=native_merged;order=native_order
 rows=(p/f'motion-actual-scanline-assets/{scan_refresh}-rows.bin').read_bytes();actual=struct.unpack('<38400I',(p/f'motion-actual-scanline-assets/{scan_refresh}-rgb.bin').read_bytes());assembled=bytearray();palette_changes=[]
 assert len(rows)==160*100480
 for y in range(160):
  row=rows[y*100480:(y+1)*100480];pal=row[98432:99456];io=row[8:104];rgb=(C.c_uint32*38400)();display=struct.unpack_from('<H',io)[0];page=0xa000 if display&16 else 0
  assert struct.unpack_from('<2I',row)==(scan_refresh,y)
  assert row[128+page:128+page+38400]==native_vram[page:page+38400] and row[128+0x14000:98432]==native_vram[0x14000:] and row[99456:100480]==oam
  assert d.nfs_scene_rgb4(native_vram[page:page+38400],merged,order,oam,pal,io,rgb)
  assembled.extend(bytes(rgb)[y*960:(y+1)*960]);palette_changes.append(pal.hex())
 expected=b''.join(struct.pack('<I',v&0xffffff) for v in actual);different=sum(a!=b for a,b in zip(assembled,expected));assert assembled==expected,('actual RGB',different)
 (p/f'motion-actual-scanline-assets/{scan_refresh}-native-rgb.bin').write_bytes(assembled)
 checks.append(dict(refresh=refresh,scan_refresh=scan_refresh,actual_rgb_pixels=38400,sampled=samples,affine_outside=outside,nontransparent_samples=opaque))
report=dict(result='PASS_JOINED_NATIVE_ACTUAL_SCANLINE_RGB',checks=checks,actual_rgb_pixels=len(checks)*38400,sprite_cases=sprite_cases,compared_pixels=sprite_cases*38400,scope='Seven actual displayed frames across alternating pages and HUD states. Native world/source persistent BG/OBJ bytes, native sprite sampling/priority/RGB/alpha with captured OAM and per-scanline palettes/IO exactly match268800 actual emulator RGB pixels. One initial VRAM seed and captured palette producers remain; no live4K/timing proof.')
(p/'joined-native-actual-scanline-rgb-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)

