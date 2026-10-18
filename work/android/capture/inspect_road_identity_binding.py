from pathlib import Path
import struct,json
folder=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-road-assets-local');capture=json.loads((folder/'source-fixture-capture-report.json').read_text());results=[]
for name in ('whole','split'):
 raw=(folder/f'race-background-{name}.nrb').read_bytes();h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab)
 for owner in range(nh[7]):
  packet=nab[nh[8+owner*2]:nh[8+owner*2]+nh[9+owner*2]];serial=struct.unpack_from('<I',packet,16)[0];wo,ws=struct.unpack_from('<II',packet,36+12);count=struct.unpack_from('<I',packet,wo+4)[0];io,isz=struct.unpack_from('<II',packet,84);commands=next(r['commands'] for r in capture['road_records'] if r['owner']['serial']==serial)
  for i in range(count):
   identity=list(struct.unpack_from('<5I',packet,io+8+i*20))
   if identity[0]!=1:continue
   matches=[dict(passno=c['passno'],ordinal=c['ordinal'],asset_available=c.get('asset_available',False)) for c in commands if c['identity']==identity];results.append(dict(fixture=name,owner=owner,serial=serial,surface=i,identity=identity,matches=matches))
report=dict(result='ROAD_IDENTITY_BINDING_DIAGNOSTIC',roads=results,unique=all(len(r['matches'])==1 for r in results));(folder/'road-identity-binding-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
