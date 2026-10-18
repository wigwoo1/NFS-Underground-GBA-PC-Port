import struct,json
from pathlib import Path
folder=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-background-local');rows=[]
for name in ('whole','split'):
 raw=(folder/f'race-background-{name}.nrb').read_bytes();h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab)
 for i in range(nh[7]):
  pkt=nab[nh[8+i*2]:nh[8+i*2]+nh[9+i*2]];at,size=struct.unpack_from('<II',pkt,84);identity=pkt[at:at+size];hits=[]
  for magic in (b'NFB1',b'NFB2'):
   pos=identity.find(magic)
   if pos>=0:
    count=struct.unpack_from('<I',identity,pos+4)[0];assert pos+16+count*8==len(identity);bounds=[struct.unpack_from('<4H',identity,pos+16+j*8) for j in range(count)];hits.append(dict(magic=magic.decode(),count=count,right_limits=sorted(set(b[1] for b in bounds)),bounds=bounds))
  assert hits;rows.append(dict(fixture=name,owner=i,bounds=hits))
report=dict(result='PASS_CAPTURED_BOUNDS_INSPECTION',packets=rows,android_boundary_pass=False,source_reference='work/camera/road_edge_gpu.h');(folder/'right-edge-bounds-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
