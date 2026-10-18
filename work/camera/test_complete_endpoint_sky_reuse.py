"""Exact sky attachment comparison on current captured complete scene endpoints."""
import json,struct,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
from owned_graph_packet import GraphPacket
from owned_sky_boundary import SkyBoundary,SceneSky
from owned_sky_sampler import SkyAsset
from owned_sky_frame import attach_sky as baseline
from owned_sky_attached_reuse_candidate import attach_sky as candidate
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stall-exact-capture-20261008/scene-inputs')
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791429984505968000.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();checks=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();h=struct.unpack_from('<6I2Q',frame);identity=(h[6],h[1]);record=next(x for x in r['sky_capture_records'] if (x['epoch'],x['publication'])==identity)
 source=record['source'];origin=record['asset_origin'];asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 b=SkyBoundary(record['epoch'],record['copy_refresh'],record['angle'],240,64,0,source,origin,0x06002940,rom[source-0x08000000:source-0x08000000+15136])
 graph=NS(epoch=identity[0],refresh=identity[1],graph=GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()))
 sky=SceneSky(b,record['serial'],record['begin'],record['end'],asset);scene=NS(identity=identity,graph=graph,sky=sky)
 expected=baseline(frame,scene);actual=candidate(frame,scene);assert actual==expected and actual is frame
 checks.append(dict(endpoint=label,identity=identity,bytes=len(frame),sha256=hashlib.sha256(actual).hexdigest(),immutable_identity_reused=True))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-attached-reuse-live-20261008');(cp/'complete-endpoint-equivalence.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Current complete frame bytes and original paired sky metadata; exact baseline attachment output. Does not independently verify GPU pixels or scanout.'),indent=2));print(checks)
