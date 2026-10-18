import sys,json,hashlib,struct
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from owned_continuous_wall_visibility import select_wall
folder=Path(sys.argv[1]);child=json.loads(Path(sys.argv[2]).read_text());assert child['dropped']==0 and child['rows']
m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and m['pending']==0
reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes());checked=0
for row in child['rows']:
 wall=SimpleNamespace(vertices=bytes.fromhex(row['vertices']),offsets=bytes.fromhex(row['offsets']))
 reference=select_wall(wall,None,row['edge_camera'],bytes.fromhex(row['framebuffer']),row['region_bounds'],bytes.fromhex(row['base_material']),reciprocal);actual=row['decision']
 assert (reference.visible,reference.reason,reference.flags)==(actual['visible'],actual['reason'],actual['flags'])
 assert len(reference.x)==len(actual['x']) and len(reference.y)==len(actual['y'])
 assert all(abs(x-y)<1e-9 for x,y in zip((*reference.x,*reference.y),(*actual['x'],*actual['y'])))
 checked+=1
rows=[];linked=0
for r in m['rows']:
 path=folder/r['world_packets']['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['world_packets']['sha256']
 with np.load(path,allow_pickle=False) as a:
  prefix=a['source_prefix'].tobytes();digest=hashlib.sha256(prefix).hexdigest();alpha=float(a['source_alpha'][0]);epoch=struct.unpack_from('<Q',prefix,24)[0];publication=struct.unpack_from('<I',prefix,4)[0]
  candidates=[c for c in child['rows'] if c['epoch']==epoch and c['older']==r['source_older'] and c['alpha']==alpha and c['source_prefix_sha256']==digest and c['source_publication']==publication]
  assert candidates,(r['sequence'],r['source_older'],alpha,digest)
  position=40;records=[]
  while position<len(prefix):
   magic,kind,context,n=struct.unpack_from('<4I',prefix,position);position+=16;assert magic==0x3147534e and n==12;blocks=[]
   for _ in range(12):size=struct.unpack_from('<I',prefix,position)[0];position+=4;blocks.append(prefix[position:position+size]);position+=size
   records.append((kind,blocks))
  walls=[]
  for draw,(kind,context,view,face) in enumerate(a['provenance']):
   if kind!=2:continue
   blocks=records[view][1]
   matches=[c for c in candidates if c['decision']['visible'] and bytes.fromhex(c['vertices'])[:68]==blocks[0][:68] and bytes.fromhex(c['offsets'])[:32]==blocks[1][:32]]
   assert matches,(r['sequence'],draw,view)
   walls.append(dict(draw=draw,view_index=int(view),source_addresses=sorted(set(c['source_address'] for c in matches)),descriptors=sorted(set(c['descriptor'] for c in matches)),candidate_visits=len(matches)));linked+=1
  rows.append(dict(sequence=r['sequence'],index=r['index'],source_older=r['source_older'],source_newer=r['source_newer'],alpha=alpha,walls=walls))
out=dict(result='PASS_LIVE_UPSTREAM_WALL_FRAME_LINKAGE',upstream_decisions_checked=checked,frames=len(rows),linked_wall_draws=linked,rows=rows,scope='Exact epoch/older/alpha/source-prefix hash/publication linkage to upstream visible decisions with recovered Python parity. Multiple matching portal visits retained. Does not certify original ROM region traversal equivalence or sustained60fps.')
(folder/'upstream-wall-linkage-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
