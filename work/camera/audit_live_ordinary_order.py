import sys,json,struct
from pathlib import Path
sys.path.insert(0,'work/camera')
from owned_motion_pairs import records
from owned_scene_bundle import chunks
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791275320241824500.json').read_text());folder=Path(report['full_scene_failure_capture']['folder']);out=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();rows=records(frame)['records'];models=[dict(index=i,key=r['key'],context=r['context'],context_words=list(struct.unpack('<'+str(len(r['blocks'][0])//4)+'I',r['blocks'][0])),matrix=list(struct.unpack('<12i',r['blocks'][2]))) for i,r in enumerate(rows) if r['kind']==3];ordinary=[]
 for h,raw in chunks((folder/(label+'.objects.bin')).read_bytes(),'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168]
   if struct.unpack_from('<H',source,10)[0]&16:continue
   ordinary.append(dict(parent=h[3],index=index,flags=list(struct.unpack_from('<2H',source,8)),position=list(struct.unpack_from('<3i',source,12)),model=struct.unpack_from('<h',source,54)[0],active=struct.unpack_from('<H',source,72)[0]))
 out.append(dict(label=label,refresh=records(frame)['refresh'],kinds=[r['kind'] for r in rows],models=models,ordinary=ordinary))
(folder/'ordinary-order-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
