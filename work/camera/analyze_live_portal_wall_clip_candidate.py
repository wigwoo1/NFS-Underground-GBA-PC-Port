import sys,json,hashlib,struct
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from owned_continuous_wall_visibility import select_wall
from owned_supplemental_eligibility import supplemental_eligibility
folder=Path(sys.argv[1]);child=json.loads(Path(sys.argv[2]).read_text());assert child['dropped']==0 and child['rows']
samples=child['samples'];assert samples and len(samples)<=child.get('sample_limit',256);assert [s['sample_id'] for s in samples]==list(range(len(samples)))
for call in child['rows']:
 sample=samples[call['sample_id']];assert all(call[k]==sample[k] for k in ('epoch','older','alpha','source_prefix_sha256','source_publication'))
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
   clip=a['source_bounds'][view];region_matches=[c for c in matches if np.array_equal(np.array(c['region_bounds']),clip)]
   assert region_matches,(r['sequence'],draw,view,clip,[c['region_bounds'] for c in matches])
   portal_matches=[]
   for candidate in region_matches:
    sample=samples[candidate['sample_id']]
    assert 'static_road_links' in sample, 'Capture lacks authoritative static child descriptors'
    links={}
    for link in sample['static_road_links']:
     raw=bytes.fromhex(link['descriptor_bytes']);assert struct.unpack_from('<H',raw,6)[0]==link['child']
     links.setdefault(link['parent'],[]).append(link)
    for region in sample['portal_regions']:
     if region[5]&8 or not np.array_equal(np.array(region[1:5]),clip):continue
     identifier=region[0];path=[]
     while True:
      if identifier==candidate['descriptor']:
       portal_matches.append(dict(region=region,static_child_path=path));break
      available=links.get(identifier,[])
      if len(available)!=1 or available[0]['secondary'] or region[5]&128:break
      link=available[0];next_child=link['child']
      if next_child==65535 or next_child in sample['hidden_static_children']:break
      assert next_child<512 and next_child not in [region[0]]+path and len(path)<512
      path.append(next_child);identifier=next_child
    for supplemental in sample.get('supplemental_candidates',[]):
     if supplemental['descriptor']!=candidate['descriptor'] or not np.array_equal(np.array(supplemental['bounds']),clip):continue
     source=bytes.fromhex(supplemental['source']);assert len(source)==164 and struct.unpack_from('<H',source,54)[0]==supplemental['descriptor']
     assert struct.unpack_from('<H',source,10)[0]&16 and supplemental['depth']>0 and supplemental['eligibility'] not in ('inactive','hidden')
     assert supplemental_eligibility(source)==supplemental['eligibility']
     region=sample['portal_regions'][supplemental['ordinal']]
     assert region[0]==supplemental['parent'] and not region[5]&8 and np.array_equal(np.array(region[1:5]),clip)
     portal_matches.append(dict(region=region,supplemental_object=supplemental['object'],descriptor=supplemental['descriptor']))
   assert portal_matches,(r['sequence'],draw,view,clip)
   walls.append(dict(draw=draw,view_index=int(view),source_addresses=sorted(set(c['source_address'] for c in matches)),descriptors=sorted(set(c['descriptor'] for c in matches)),candidate_visits=len(matches),exact_region_visits=len(region_matches),clip_bounds=clip.tolist(),portal_regions=portal_matches));linked+=1
  rows.append(dict(sequence=r['sequence'],index=r['index'],source_older=r['source_older'],source_newer=r['source_newer'],alpha=alpha,walls=walls))
out=dict(result='PASS_LIVE_PORTAL_REGION_WALL_CLIP_LINKAGE',upstream_decisions_checked=checked,frames=len(rows),linked_wall_draws=linked,rows=rows,scope='Exact epoch/older/alpha/source-prefix hash/publication linkage to upstream visible decisions with recovered Python parity. Multiple matching portal visits retained. Does not certify original ROM region traversal equivalence or sustained60fps.')
(folder/'portal-wall-clip-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
