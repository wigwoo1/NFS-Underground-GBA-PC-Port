"""Compare all native model portal bounds with actual original raster rectangles."""
import json,struct,sys,hashlib
from pathlib import Path
from scene_batches import batches
capture=json.loads(Path(sys.argv[1]).read_text());sources=json.loads(Path(sys.argv[2]).read_text())
rows={tuple(row['identity'][2:]):row for row in sources['original_endpoints']};checks=[]
for batch in batches(Path(capture['trace'])):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in rows:continue
 row=rows[key];packet=Path(row['path']).read_bytes();assert hashlib.sha256(packet).hexdigest()==row['sha256']
 sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5))}
 world=struct.unpack_from('<I',sections[2],4)[0];models=struct.unpack_from('<I',sections[1],4)[0];trailer=8+(world+models)*20;assert sections[5][trailer:trailer+4]==b'NFB2'
 native={struct.unpack_from('<5I',sections[5],8+20*(world+i))[2]:struct.unpack_from('<4H',sections[5],trailer+16+8*(world+i)) for i in range(models)}
 object_address=None;observed={}
 for event in batch['events']:
  if event['pc']==0x03002628:object_address=event['blocks'][62][0]
  if event['pc']!=0x03003d4c:continue
  assert object_address in native
  left,top,right,bottom=struct.unpack('<4i',event['blocks'][86][1]);bounds=(left,right,top,bottom);assert bounds==native[object_address],(key,hex(object_address),bounds,native[object_address])
  observed[object_address]=observed.get(object_address,0)+1
 if observed:checks.append(dict(interval=key,models=[dict(object=hex(obj),native_bounds=list(native[obj]),original_polygon_classifications=count,exact_original_rectangle=True) for obj,count in observed.items()],all_model_rectangles_observed=set(observed)==set(native)))
assert sum(c['all_model_rectangles_observed'] for c in checks)>=3
out=Path(sys.argv[1]).with_name(Path(sys.argv[1]).stem.replace('-verification','-model-bound-parity')+'.json');out.write_text(json.dumps(dict(result='PASS',checks=checks,scope='NFB2 source portal bounds match actual original polygon-classifier rectangles for all observed model objects. Bounds parity only, not full scene raster/motion/scanout.'),indent=2));print(json.dumps(dict(result='PASS',full_model_scenes=sum(c['all_model_rectangles_observed'] for c in checks),models=sum(len(c['models']) for c in checks),polygon_rectangles=sum(m['original_polygon_classifications'] for c in checks for m in c['models']))))
