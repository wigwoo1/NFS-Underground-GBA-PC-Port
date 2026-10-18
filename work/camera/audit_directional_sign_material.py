"""Audit directional-sign source UVs, texture and zero-write metadata at original poses."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from scene_batches import batches
capture_path=Path(sys.argv[1]);capture=json.loads(capture_path.read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256']
sources=json.loads(Path(sys.argv[2]).read_text());packets={tuple(r['identity'][2:]):r for r in sources['original_endpoints']};checks=[]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in packets:continue
 row=packets[key];data=Path(row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
 sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))};world=sections[2];count=struct.unpack_from('<I',world,4)[0];position=8;surfaces=[]
 for i in range(count):
  n,w,h=struct.unpack_from('<3I',world,position);size=12+n*40+w*h*4;surfaces.append((world[position:position+size],n,w,h));position+=size
 assert world[position:position+4]==b'NWI1';position+=8;metadata=[]
 for i in range(count):
  mode,size=struct.unpack_from('<2I',world,position);position+=8;metadata.append((mode,world[position:position+size]));position+=size
 ids=[struct.unpack_from('<5I',sections[5],8+i*20) for i in range(count)];matches=[i for i,v in enumerate(ids) if v[0]==2 and v[2]==0x08574c3c];assert len(matches)==1;at=matches[0];surface,n,width,height=surfaces[at]
 for e in batch['events']:
  if e['pc']!=0x03000304 or e['blocks'][5][0]!=0x08574c3c:continue
  b=e['blocks'];s=b[5][1];anim=b[70][1];flags=e['regs'][2];assert not flags&128 and flags&256
  u0=struct.unpack_from('<H',s,40)[0]/width+struct.unpack_from('<h',anim,4)[0]/(256*width);u1=u0+struct.unpack_from('<H',s,64)[0]/256
  if flags&2:u0,u1=u1,u0
  top=(struct.unpack_from('<i',s,16)[0]+(struct.unpack_from('<h',anim,6)[0]>>1))/(128*height);span=(struct.unpack_from('<i',s,24)[0]+(struct.unpack_from('<h',anim,6)[0]>>1))/(128*height)
  expected=np.array([[u0,top],[u1,top],[u1,top+span],[u0,top+span]]);actual=np.array([struct.unpack_from('<2d',surface,12+n*24+j*16) for j in range(n)]);assert np.array_equal(expected,actual)
  texture=np.frombuffer(b[66][1],np.uint8);assert len(texture)==width*height;palette=np.frombuffer(b[67][1],'<u2');colors=palette[texture];rgba=np.column_stack([(colors&31)*255//31,((colors>>5)&31)*255//31,((colors>>10)&31)*255//31,np.where(texture!=0,255,0)]).astype(np.uint8)
  native=np.frombuffer(surface[12+n*40:],np.uint8).reshape(-1,4);mode,states=metadata[at];assert mode==2 and states==bytes(np.where(texture!=0,2,0).astype(np.uint8))
  checks.append(dict(interval=key,flags=hex(flags),original_prepared_edge_words=list(struct.unpack('<13I',b[6][1])),native_uv_exact=True,uv=actual.tolist(),source_texture_sha256=hashlib.sha256(texture.tobytes()).hexdigest(),rgba_differing_texels=int(np.any(rgba!=native,axis=1).sum()),wall_write_states_exact=True,texture_size=[width,height]))
assert len(checks)>=3
out=capture_path.with_name(capture_path.stem.replace('-verification','-sign-material-audit')+'.json');out.write_text(json.dumps(dict(result='AUDITED',checks=checks,scope='Original sign UV source fields, resolved texture/palette versus native world UV/RGBA and wall zero-write states. Does not execute full original projected column traversal, texture sampling or scanout.'),indent=2));print(json.dumps(checks))
