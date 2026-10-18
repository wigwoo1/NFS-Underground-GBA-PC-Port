from pathlib import Path
import json,struct,hashlib
from scene_batches import batches
p=Path('work/camera');scenes=[];assets=p/'motion-wall-assets';assets.mkdir(exist_ok=True)
u=lambda b,o:struct.unpack_from('<H',b,o)[0]
h=lambda b,o:struct.unpack_from('<h',b,o)[0]
i=lambda b,o:struct.unpack_from('<i',b,o)[0]
def asset(data):
 key=hashlib.sha256(data).hexdigest();(assets/(key+'.bin')).write_bytes(data);return dict(sha256=key,bytes=len(data),path=str(assets/(key+'.bin')))
for scene in batches(p/'motion-original-source-8750-8781.bin'):
 if scene['begin_refresh']<8750 or scene['end_refresh']>8781:continue
 active={};walls=[]
 for e in scene['events']:
  b=e['blocks']
  if e['pc']==0x03001800:active[b[1][0]]=b
  if e['pc']!=0x03000304:continue
  owner=active[b[1][0]];count=u(owner[4][1],2);index=(b[5][0]-owner[5][0])//68;assert 0<=index<count and owner[5][0]+index*68==b[5][0]
  s=b[5][1];off=b[9][1] or bytes(32);next_index=(index+1)%count;ns=owner[5][1][next_index*68:(next_index+1)*68];no=owner[10+next_index][1] or bytes(32);x=i(s,0)+h(off,0);z=i(s,4)+h(off,2);nx=i(ns,0)+h(no,0);nz=i(ns,4)+h(no,2);vertices=[[x,h(s,8)+h(off,8),z],[nx,h(s,12)+h(off,8),nz],[nx,h(s,14)+h(off,10),nz],[x,h(s,10)+h(off,10),z]]
  mat=b[8][1];width=1<<u(mat,36);height=u(mat,38);texture=b[66][1];palette=b[67][1];assert len(texture)==width*height and len(palette)==512;flags=e['regs'][2];light=b.get(74,(0,b''))[1];shaded=not(flags&256)
  if shaded:assert len(light)==4096
  walls.append(dict(event=e['id'],source=owner[4][0],edge=index,world_vertices=vertices,camera_hex=b[2][1].hex(),bounds=list(struct.unpack_from('<4H',b[1][1],226)),flags=flags,extended_uv=bool(flags&128),shaded=shaded,source_hex=s.hex(),offset_hex=off.hex(),animation_hex=b[70][1].hex(),material_hex=mat.hex(),width=width,height=height,texture=asset(texture),palette=asset(palette),lighting=asset(light) if light else None))
 scenes.append(dict(begin=scene['begin_refresh'],end=scene['end_refresh'],page=scene['display_page'],walls=walls,roads=sum(e['pc']==0x030032f0 for e in scene['events']),models=sum(e['pc']==0x03004770 for e in scene['events'])))
walls=[w for s in scenes for w in s['walls']];r=dict(result='COMPLETE_CAPTURED_WALL_MATERIAL_SNAPSHOTS',scenes=scenes,wall_draws=len(walls),shaded=sum(w['shaded'] for w in walls),extended_uv=sum(w['extended_uv'] for w in walls),unique_assets=len(list(assets.glob('*.bin'))),scope='Owned world edge/source linkage and exact captured material/texture/palette/light assets for7completed scenes. No wall raster/UV/shading parity or fullscene render proof; extended UV flagged.')
(p/'motion-wall-snapshots.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k not in ('scenes','scope')})
