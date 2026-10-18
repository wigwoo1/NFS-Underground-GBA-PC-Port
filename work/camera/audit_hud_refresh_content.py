import json,struct
from pathlib import Path
p=Path('work/camera');rows=[];previous=None
for refresh in (8758,8762,8766,8769,8773,8776,8780):
 data=(p/f'motion-actual-scanline-assets/{refresh}-native-complete-frame.bin').read_bytes();magic,r,gn,hn,bn,tn,epoch,ticks=struct.unpack_from('<6I2Q',data);assert magic==0x3346474e and hn==160*34944
 hud=data[40+gn:40+gn+hn];text=data[40+gn+hn+bn:];assert len(text)==tn
 for y in range(160):assert struct.unpack_from('<2I',hud,y*34944)==(refresh,y)
 if previous:
  old_refresh,old_hud,old_text,old_epoch=previous
  fields={} 
  for name,begin,end in (('registers',8,104),('affine',104,128),('obj_vram',128,32896),('palette',32896,33920),('oam',33920,34944)):
   fields[name]=sum(hud[y*34944+begin:y*34944+end]==old_hud[y*34944+begin:y*34944+end] for y in range(160))
  same=[y for y in range(160) if hud[y*34944+4:(y+1)*34944]==old_hud[y*34944+4:(y+1)*34944]]
  rows.append(dict(older=old_refresh,newer=refresh,epoch_equal=epoch==old_epoch,raw_hud_equal=hud==old_hud,rows_equal_ignoring_refresh=len(same),equal_rows_by_field=fields,text_equal=text==old_text,full_content_reuse_possible=len(same)==160 and text==old_text and epoch==old_epoch))
 previous=refresh,hud,text,epoch
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-refresh-content-audit-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='AUDITED_CAPTURED_INPUTS',pairs=rows,scope='Seven actual complete captured frames: compare all HUD row bytes except refresh uint32, preserving row index/registers/affine/OBJ VRAM/palette/OAM and exact text. Input equality audit, not GPU parity or live cache benefit.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(rows))

