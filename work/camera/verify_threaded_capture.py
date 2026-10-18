import json,struct,hashlib,sys
from pathlib import Path
from PIL import Image,ImageDraw
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=session['prefix']
rows=[];contact=Image.new('RGB',(1280,1080));draw=ImageDraw.Draw(contact)
for i in range(1,13):
 base=Path(prefix+f'-capture-{i:02d}')
 meta=json.loads(Path(str(base)+'-native-source.json').read_text());packet=Path(str(base)+'-native-scene.bin').read_bytes()
 assert len(packet)==meta['packet_bytes'] and 0<=meta['alpha']<=1
 tag,offset,size=struct.unpack_from('<III',packet,32);assert tag==1
 magic=packet[offset:offset+4];count=struct.unpack_from('<I',packet,offset+4)[0] if magic==b'NML1' else 1
 image=Image.open(str(base)+'-native.ppm');assert image.size==(3840,2160)
 x=((i-1)%2)*640;y=((i-1)//2)*180
 contact.paste(image.resize((640,160)),(x,y));draw.text((x+3,y+160),f"{i}: target {meta['target']:.3f} alpha {meta['alpha']:.3f} cars {count}",fill='white')
 sections={}
 for j in range(5):
  tag,off,n=struct.unpack_from('<III',packet,32+j*12);sections[tag]=packet[off:off+n]
 world=sections[2];world_count=struct.unpack_from('<I',world,4)[0];position=8
 for j in range(world_count):
  n,width,height=struct.unpack_from('<3I',world,position);position+=12+n*40+width*height*4
 assert world[position:position+4]==b'NWI1';position+=8;road_modes=[]
 for j in range(world_count):
  mode,length=struct.unpack_from('<2I',world,position);position+=8+length
  if struct.unpack_from('<I',sections[5],8+j*20)[0]==1:road_modes.append(mode)
 if session.get('live_road_attributes'):assert road_modes and all(mode in (5,6) for mode in road_modes)
 ids=sections[5];bounds_offset=8+(world_count+count)*20;model_bounds=[]
 if ids[bounds_offset:bounds_offset+4]==b'NFB2':
  assert struct.unpack_from('<I',ids,bounds_offset+4)[0]==world_count+count
  assert len(ids)==bounds_offset+16+(world_count+count)*8
  model_bounds=[struct.unpack_from('<4H',ids,bounds_offset+16+(world_count+j)*8) for j in range(count)]
  assert all(l<=r<=240 and t<=b<=160 for l,r,t,b in model_bounds)
 if session.get('live_model_bounds'):assert len(model_bounds)==count
 rows.append(dict(**meta,models=count,model_portal_bounds=model_bounds,road_mapping_modes=road_modes,packet_sha256=hashlib.sha256(packet).hexdigest()))
assert all(a['target']<b['target'] for a,b in zip(rows,rows[1:]));assert any(0<r['alpha']<1 for r in rows);assert all(r['models']>=1 for r in rows)
if session.get('capture_refresh')==12350:assert any(r['models']>=2 for r in rows)
report=dict(result='PASS',frames=rows,scope='Twelve duplicate-render-checked full native 4K submissions with live hardware layers; fractional poses present; model counts and road attribute modes enumerated. Capture perturbs timing; image coverage and smooth motion remain unproven.')
Path(prefix+'-capture-verification.json').write_text(json.dumps(report,indent=2));contact.save(prefix+'-capture-contact.png');print(json.dumps(dict(result='PASS',model_counts=[r['models'] for r in rows],alphas=[r['alpha'] for r in rows],road_modes=[r['road_mapping_modes'] for r in rows])))
