import csv,json,struct
from pathlib import Path
from dataclasses import replace,FrozenInstanceError
from owned_sky_boundary import SkyBoundary,HEADER
from owned_sky_scroll import source_offset
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();records=[];negative=0
for r in csv.DictReader(Path('work/camera/sky-caller-trace.csv').open()):
 if r['wrapper_saved_return']!='08004cb9' or r['height']!='63':continue
 angle=int(r['sky_angle'],16);center=int(r['sky_center']);center=center-65536 if center>=32768 else center;source=int(r['source'],16);origin=source-source_offset(angle,240,center);indices=bytearray(rom[source-0x08000000:source-0x08000000+15136])
 b=SkyBoundary(2,int(r['refresh']),angle,240,64,center,source,origin,int(r['destination'],16),indices);packet=b.encode();indices[0]^=255;assert b.encode()==packet and SkyBoundary.decode(packet)==b;image,coverage=b.plane();assert len(image)==len(coverage)==38400 and sum(coverage)==15136;assert image[10560:25696]==b.indices and coverage[10560:25696]==bytes([1])*15136;assert not any(coverage[:10560]+coverage[25696:]);records.append(b)
for a,b in zip(records,records[1:]):assert a.compatible(b)
a=records[0]
for bad in (a.encode()[:-1],a.encode()+b'x',b'BAD!'+a.encode()[4:]):
 try:SkyBoundary.decode(bad)
 except ValueError:negative+=1
 else:raise AssertionError('Bad packet accepted')
for kw in (dict(source=a.source+2),dict(destination=0x06000000),dict(width=241),dict(indices=b'')):
 try:replace(a,**kw)
 except ValueError:negative+=1
 else:raise AssertionError('Bad metadata accepted')
for b in (replace(a,epoch=3),a):
 try:a.compatible(b)
 except ValueError:negative+=1
 else:raise AssertionError('Bad pair accepted')
assert len(records)==161
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-sky-boundary-20261006');out.mkdir(parents=True,exist_ok=True)
for name in ('owned_sky_boundary.py','test_owned_sky_boundary.py'):(out/name).write_text((Path('work/camera')/name).read_text())
(out/'tests.json').write_text(json.dumps(dict(result='PASS',captured_boundaries=len(records),negative_checks=negative,scope='Owned original sky input metadata/ROM copy bytes, codec exact roundtrip, mutable source isolation and pair rejection; not active scene capture or GPU sky interpolation'),indent=2));print('PASS owned sky boundaries',len(records),'negative',negative)
