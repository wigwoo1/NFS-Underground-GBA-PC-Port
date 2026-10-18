import sys,json,struct,hashlib
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and m['pending']==0
rows=[];total=0
for row in m['rows']:
 packet=row['world_packets'];path=folder/packet['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==packet['sha256']
 with np.load(path,allow_pickle=False) as a:
  prefix=a['source_prefix'].tobytes();assert struct.unpack_from('<I',prefix)[0]==0x3346474e
  gn=struct.unpack_from('<I',prefix,8)[0];assert len(prefix)==40+gn
  assert struct.unpack_from('<Q',prefix,24)[0]==row['epoch']
  records=[];position=40
  while position<len(prefix):
   magic,kind,context,n=struct.unpack_from('<4I',prefix,position);position+=16;assert magic==0x3147534e and kind in (1,2,3) and n==12
   blocks=[]
   for _ in range(12):
    size=struct.unpack_from('<I',prefix,position)[0];position+=4;assert size<=0x100000 and position+size<=len(prefix);blocks.append(prefix[position:position+size]);position+=size
   records.append((kind,context,blocks))
  assert position==len(prefix) and a['source_bounds'].shape==(len(records),4)
  assert a['camera'].shape==(12,) and np.isfinite(a['camera']).all() and 0<=a['source_alpha'][0]<=1
  walls=[]
  for draw,provenance in enumerate(a['provenance']):
   kind,context,view,face=map(int,provenance);assert view<len(records)
   rk,rc,blocks=records[view];assert (rk,rc)==(kind,context)
   if kind!=2:continue
   assert len(blocks[0])==136 and len(blocks[1])==64 and len(blocks[2])==8 and len(blocks[4])==48 and len(blocks[9])==512
   shift,height=struct.unpack_from('<HH',blocks[4],36);width=1<<shift;assert shift<=10 and 0<height<=1024
   indices=np.frombuffer(blocks[8],np.uint8)[:width*height].reshape(height,width);palette=np.frombuffer(blocks[9],'<u2');colors=palette[indices]
   expected=np.empty((height,width,4),np.uint8)
   for channel in range(3):
    five=(colors>>(channel*5))&31;expected[:,:,channel]=(five<<3)|(five>>2)
   expected[:,:,3]=np.where(indices==0,0,255)
   tid=int(a['texture_ids'][draw]);w,h,offset,size=map(int,a['texture_records'][tid-1]);assert (w,h)==(width,height)
   assert np.array_equal(expected.reshape(-1),a['texture_rgba'][offset:offset+size])
   bounds=a['source_bounds'][view];assert np.isfinite(bounds).all()
   expected_scissor=np.array([300+np.ceil(bounds[0]*13.5),2160-np.ceil((160-bounds[2])*13.5),300+np.ceil((bounds[1]+1)*13.5),2160-np.ceil((160-(bounds[3]+1))*13.5)],dtype=np.int32)
   actual=np.frombuffer(a['states'][draw,32:48].tobytes(),'<i4');assert np.array_equal(expected_scissor,actual),(draw,bounds,actual,expected_scissor)
   walls.append(dict(draw=draw,view_index=view,source_sha256=hashlib.sha256(blocks[0]).hexdigest(),width=width,height=height,clip=bounds.tolist(),scissor=actual.tolist()))
  total+=len(walls);rows.append(dict(index=row['index'],walls=walls))
out=dict(result='PASS_ORIGINAL_WALL_RECORD_MATERIAL_AND_CLIP_LINKAGE',frames=len(rows),wall_draws=total,rows=rows,scope='Exact indexed material decode and sampled clip-to-scissor conversion from immutable source records. Does not prove the sampled clip itself matches original visibility, wall pose geometry or scanout cadence.')
(folder/'wall-record-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
