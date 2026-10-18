import sys,struct,json
from pathlib import Path
sys.path.insert(0,'work/camera')
from scene_batches import records
out=[]
for filename in ('world.bin','motion-original-source-8750-8781.bin'):
 count=0;affected=[]
 for e in records(Path('work/camera')/filename):
  if e['pc']!=0x03000304:continue
  b=e['blocks']
  if 5 not in b or len(b[5][1])<68:continue
  count+=1;s=b[5][1];v=struct.unpack_from('<4i',s,16)
  anim=b.get(70,(0,b''))[1];a=struct.unpack_from('<2h',anim,4) if len(anim)>=8 else None
  if v[0]!=v[1] or v[2]!=v[3] or (a is not None and a[0]&1):
   affected.append({'event':e['id'],'refresh':e['frame'],'vertical_fields':v,'animation':a,'source_hex':s[:68].hex(),'animation_hex':anim.hex()})
 out.append({'source':filename,'wall_events':count,'affected':affected})
report={'result':'ORIGINAL_CAPTURE_WALL_UV_COVERAGE','captures':out,'scope':'Original wall callback raw source events in two existing diagnostic traces only; affected identification does not verify native rendering.'}
Path('work/camera/prototype-runs/original-capture-wall-uv-coverage-20261010.json').write_text(json.dumps(report,indent=2))
print([(x['source'],x['wall_events'],len(x['affected'])) for x in out])
