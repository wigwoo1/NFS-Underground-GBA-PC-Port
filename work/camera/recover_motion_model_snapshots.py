from pathlib import Path
import json,struct,hashlib
from scene_batches import batches
p=Path('work/camera');assets=p/'motion-model-assets';assets.mkdir(exist_ok=True)
keys={(s['begin'],s['end']) for s in json.loads((p/'motion-wall-snapshots.json').read_text())['scenes']}
def asset(b):
 h=hashlib.sha256(b).hexdigest();target=assets/(h+'.bin');target.write_bytes(b);return dict(path=str(target),sha256=h,bytes=len(b))
scenes=[]
for scene in batches(p/'motion-original-model-rect-world.bin'):
 key=(scene['begin_refresh'],scene['end_refresh'])
 if key not in keys:continue
 models=[];order=[]
 for e in scene['events']:
  if e['pc'] in (0x030032f0,0x03000304,0x03004770):order.append(dict(event=e['id'],kind={0x030032f0:'road',0x03000304:'wall',0x03004770:'model'}[e['pc']]))
  if e['pc']!=0x03004770:continue
  b=e['blocks'];context=b[51][1];desc=b[52][1];count=struct.unpack_from('<H',desc,36)[0];face_count=struct.unpack_from('<H',desc,34)[0]
  verts=[list(struct.unpack_from('<3h',b[54][1],i*6)) for i in range(count)]
  sizes=list(b[60][1]);assert len(sizes)==face_count and len(b[54][1])==count*6
  indices=list(struct.unpack('<'+'H'*(len(b[58][1])//2),b[58][1]));uv_indices=list(struct.unpack('<'+'H'*(len(b[59][1])//2),b[59][1]));uv_count=len(b[65][1])//4
  assert sum(sizes)==len(indices)==len(uv_indices) and all(i<count for i in indices) and all(i<uv_count for i in uv_indices)
  faces=[];offset=0
  for n in sizes:
   assert 3<=n<=32;faces.append(dict(vertices=indices[offset:offset+n],uv=uv_indices[offset:offset+n]));offset+=n
  shift,height=struct.unpack_from('<2H',context,56);assert len(b[66][1])==(1<<shift)*height and len(b[67][1])==512
  assert len(b[90][1])==16
  models.append(dict(rectangle=list(struct.unpack('<4i',b[90][1])),rectangle_address=b[90][0],event=e['id'],context_address=b[51][0],context_hex=context.hex(),descriptor_hex=desc.hex(),transform_hex=b[53][1].hex(),framebuffer_descriptor_hex=b[56][1].hex(),vertices=verts,faces=faces,uv_asset=asset(b[65][1]),texture=asset(b[66][1]),palette=asset(b[67][1]),width=1<<shift,height=height,source_projected_oracle=asset(b[68][1])))
 scenes.append(dict(begin=key[0],end=key[1],page=scene['display_page'],draw_order=order,models=models))
r=dict(result='COMPLETE_CAPTURED_MODEL_INPUT_SNAPSHOTS',scenes=scenes,model_draws=sum(len(s['models']) for s in scenes),vertices=sum(len(m['vertices']) for s in scenes for m in s['models']),faces=sum(len(m['faces']) for s in scenes for m in s['models']),unique_assets=len(list(assets.glob('*.bin'))),scope='Owned raw model vertices/topology/UV/texture/palette/transform plus complete captured road/wall/model order. Projected scratch stored separately as oracle; not native input. Model transform/raster parity, scene clears/display and live timing unverified.')
(p/'motion-model-snapshots.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scenes','scope')})
