from pathlib import Path
import json,hashlib,struct
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-initial-inputs-world.bin'));new=list(records(p/'motion-original-complete-display-world.bin'));assert len(old)==len(new)
for a,b in zip(old,new):
 for k in ('pc','frame','id','regs'):assert a[k]==b[k],(a['id'],k)
 for tag,value in a['blocks'].items():assert b['blocks'][tag]==value,(a['id'],tag)
assets=p/'motion-complete-display-assets';assets.mkdir(exist_ok=True);scenes=[];previous=None
for e in new:
 if e['pc']!=0x04000000 or not 8757<=e['frame']<=8779:continue
 assert all(len(e['blocks'][tag][1])==size for tag,size in [(98,16384),(99,1024),(100,512)])
 obj=e['blocks'][98][1];oam=e['blocks'][99][1];pal=e['blocks'][100][1];paths={}
 for name,data in [('obj-vram',obj),('oam',oam),('obj-palette',pal)]:
  target=assets/f"{e['frame']}-{name}.bin";target.write_bytes(data);paths[name]=dict(path=str(target),sha256=hashlib.sha256(data).hexdigest())
 # In bitmap mode, non-affine attr0 bit9 means disabled; affine bit9 means double size.
 enabled=sum(bool(struct.unpack_from('<H',oam,i*8)[0]&256) or not bool(struct.unpack_from('<H',oam,i*8)[0]&512) for i in range(128))
 scenes.append(dict(refresh=e['frame'],assets=paths,enabled_oam_entries=enabled,obj_changed_bytes=None if previous is None else sum(a!=b for a,b in zip(obj,previous))))
 previous=obj
assert len(scenes)==7
report=dict(result='CAPTURED_COMPLETE_DISPLAY_SPRITE_STATE',existing_records_preserved=len(old),scenes=scenes,scope='Actual closing page OBJ VRAM/OAM/OBJ palette; asset ownership and original display state only, no native sprite compositing or 4K/full-scene timing proof.')
(p/'motion-complete-display-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report['result'],len(old),[(s['refresh'],s['enabled_oam_entries'],s['obj_changed_bytes']) for s in scenes])
