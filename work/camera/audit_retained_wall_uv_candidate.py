import sys,struct,json
from pathlib import Path
sys.path.insert(0,'work/camera')
from owned_motion_pairs import records
rows=[];total=0
for folder in Path('work/camera/prototype-runs').glob('child-scene-*'):
 for p in folder.glob('*.frame.bin'):
  decoded=records(p.read_bytes());walls=[]
  for i,r in enumerate(decoded['records']):
   if r['kind']!=2:continue
   total+=1;b=r['blocks'];v=struct.unpack_from('<4i',b[0],16);a=struct.unpack_from('<2h',b[2],4);shift,height=struct.unpack_from('<HH',b[4],36);flags=struct.unpack_from('<I',b[11],256)[0]
   walls.append({'record':i,'vertical_fields':v,'animation':a,'shift':shift,'height':height,'flags':flags,'affected':v[0]!=v[1] or v[2]!=v[3] or bool(a[0]&1)})
  rows.append({'frame':str(p),'epoch':decoded['epoch'],'refresh':decoded['refresh'],'walls':walls})
out={'result':'RETAINED_WALL_UV_COVERAGE','frames':rows,'total_walls':total,'affected_walls':sum(w['affected'] for row in rows for w in row['walls']),'scope':'Retained exact endpoint records only; supplemental history and route-wide coverage not included.'}
Path('work/camera/prototype-runs/wall-uv-retained-coverage-20261009.json').write_text(json.dumps(out,indent=2));print('frames',len(rows),'walls',total,'affected',out['affected_walls'])
for row in rows:
 for wall in row['walls']:
  if wall['affected']:print(row['frame'],row['refresh'],wall)
