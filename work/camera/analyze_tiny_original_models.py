"""Actual original integer-projected faces and store counts for tiny model."""
import json,struct,sys
from pathlib import Path
from scene_batches import batches
file=Path(sys.argv[1]);report=json.loads(file.read_text());completed={c['id']:c for c in report['completed_draws']};checks=[]
for batch in batches(Path(report['trace'])):
 object_address=None;draw_id=None
 for event in batch['events']:
  if event['pc']==0x03002628:object_address=event['blocks'][62][0]
  if event['pc']==0xffff0084:
   stage,identity,pc,*_=struct.unpack('<8I',event['blocks'][85][1][:32])
   if stage==0 and pc==0x03004770:draw_id=identity
  if event['pc']!=0x03004770 or object_address!=0x020044fc or draw_id not in completed:continue
  points=[struct.unpack_from('<2h',event['blocks'][68][1],i) for i in range(0,len(event['blocks'][68][1]),4)]
  sizes=event['blocks'][60][1];indices=struct.unpack('<'+'H'*(len(event['blocks'][58][1])//2),event['blocks'][58][1]);offset=0;faces=[]
  for index,n in enumerate(sizes):
   ring=[points[i] for i in indices[offset:offset+n]];offset+=n
   a,b,c=ring[:3];det=(b[1]-a[1])*(c[0]-a[0])-(c[1]-a[1])*(b[0]-a[0])
   faces.append(dict(face=index,original_backface_skip=det<0,integer_determinant=det,height=max(v[1] for v in ring)-min(v[1] for v in ring)))
  assert offset==len(indices)
  draw=completed[draw_id];checks.append(dict(interval=[batch['begin_refresh'],batch['end_refresh']],object=hex(object_address),draw_id=draw_id,transform_eligible=event['regs'][0],projected_bbox=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)],faces=faces,original_polygon_calls=draw['original_polygon_calls'],vram_store_calls=draw['vram_store_calls'],vram_store_bytes=draw['vram_store_bytes'],changed_vram_bytes=draw['changed_vram_bytes']))
assert len(checks)==3
out=file.with_name(file.stem.replace('-verification','-tiny-models')+'.json');out.write_text(json.dumps(dict(result='ANALYZED',checks=checks,scope='Actual original post-transform integer geometry, first-three-vertex backface predicate and original polygon/store telemetry for source object020044FC. Store counts include identical-value writes; not native raster proof or a rule to hide distant native geometry.'),indent=2));print(json.dumps(dict(report=str(out),models=len(checks),polygon_calls=[c['original_polygon_calls'] for c in checks],store_calls=[c['vram_store_calls'] for c in checks],changed_bytes=[c['changed_vram_bytes'] for c in checks])))
