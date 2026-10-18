from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');d=C.CDLL(str((p/'native_sprite.dll').resolve()));d.nfs_sprite_local.argtypes=[C.c_uint,C.c_uint,C.c_int,C.c_int]+[C.c_uint]*4+[C.c_void_p,C.c_void_p];d.nfs_sprite_sample4.argtypes=[C.c_void_p,C.c_size_t]+[C.c_uint]*6+[C.c_void_p]
oracle=C.CDLL(str((p/'sprite_original_oracle.dll').resolve())).nfs_original_sprite_plane;oracle.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
combined_oracle=C.CDLL(str((p/'sprite_original_oracle.dll').resolve())).nfs_original_sprite_combined;combined_oracle.argtypes=oracle.argtypes
d.nfs_sprite_merge.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
from scene_batches import records
frames={e['frame']:e for e in records(p/'motion-original-video-state-world.bin') if e['pc']==0x04000000}
d.nfs_scene_rgb4.argtypes=[C.c_void_p]*7
checks=[];sprite_cases=0
for scene in json.loads((p/'motion-visible-sprite-modes.json').read_text())['scenes']:
 merged=(C.c_uint16*38400)(*[65535]*38400);order=(C.c_uint16*38400)(*[65535]*38400)
 refresh=scene['refresh'];obj=(p/f'motion-complete-display-assets/{refresh}-obj-vram.bin').read_bytes();oam=(p/f'motion-complete-display-assets/{refresh}-oam.bin').read_bytes();samples=outside=opaque=0
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
 frame=frames[refresh];pal=frame['blocks'][67][1]+frame['blocks'][100][1];rgb=(C.c_uint32*38400)()
 assert d.nfs_scene_rgb4(frame['blocks'][92][1],merged,order,oam,pal,frame['blocks'][103][1],rgb)
 expected=(p/f'motion-static-rgb-assets/{refresh}-rgb.bin').read_bytes();different=sum(a!=b for a,b in zip(bytes(rgb),expected))
 if different:
  original_words=struct.unpack('<38400I',expected);bad=[i for i in range(38400) if rgb[i]!=original_words[i]]
  diagnostic=dict(refresh=refresh,different_pixels=len(bad),background_only=sum(merged[i]==65535 for i in bad),sprite_covered=sum(merged[i]!=65535 for i in bad),rows=[sum(i//240==y for i in bad) for y in range(160)],examples=[dict(x=i%240,y=i//240,native=hex(rgb[i]),original=hex(original_words[i]),bg_index=frame['blocks'][92][1][i],sprite_index=merged[i]) for i in bad[:12]])
  (p/'native-static-rgb-localization.json').write_text(json.dumps(diagnostic,indent=2),encoding='utf-8');print(diagnostic)
  (p/'native-static-scene-rgb-difference.json').write_text(json.dumps(dict(result='NATIVE_STATIC_SCENE_RGB_DIFFERENCE',refresh=refresh,different_bytes=different,scope='Native profile implementation incomplete; static original reference may include affine background transform and renderer scheduling.'),indent=2),encoding='utf-8')
 assert bytes(rgb)==expected,('RGB',refresh,different)
 checks.append(dict(refresh=refresh,sampled=samples,affine_outside=outside,nontransparent_samples=opaque))
report=dict(result='PASS_NATIVE_STATIC_SCENE_RGB',checks=checks,sprite_cases=sprite_cases,compared_pixels=sprite_cases*38400,scope='Native BG index plus native sprite sampling/priority/palette/alpha composition matches seven original mgba static snapshot RGB frames (268800 RGB pixels). Captured BG page input here; native world-to-VRAM proof separate. Actual scanline history/live GPU4K/timing remains unverified.')
(p/'native-static-scene-rgb-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)

