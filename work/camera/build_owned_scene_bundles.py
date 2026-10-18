from pathlib import Path
import struct,json
from owned_graph_packet import GraphPacket
from owned_scene_bundle import SceneBundle,chunks
p=Path('work/camera');packets={};cameras={}
for f in (p/'graph-packets').glob('*.ngp'):
 packet=GraphPacket.decode(f.read_bytes());packets[packet.refresh]=f.read_bytes();assert packet.context[256:304] not in cameras;cameras[packet.context[256:304]]=packet.refresh
sections={r:{k:bytearray() for k in ('objects','callbacks','supplements','textures','associations','graph_objects')} for r in packets};keys={}
for kind,file,cs in [('graph_objects','owned-graph-objects.bin',32),('associations','owned-object-associations.bin',352),('objects','owned-object-input-lists.bin',32),('callbacks','owned-object-eligibility.bin',196),('supplements','owned-supplement-geometry.bin',80)]:
 for h,raw in chunks((p/file).read_bytes(),kind):
  refresh=cameras[raw[cs:cs+48]];sections[refresh][kind].extend(raw)
  if kind=='supplements':keys[(h[1],h[2],h[3])]=refresh
for h,raw in chunks((p/'owned-supplement-textures.bin').read_bytes(),'textures'):sections[keys[(h[1],h[2],h[3])]]['textures'].extend(raw)
target=p/'scene-bundles';target.mkdir(exist_ok=True);checks=[]
for r,parts in sections.items():
 if not parts['objects']:continue # Last captured graph precedes uncaptured later object draw; not a complete interval.
 bundle=SceneBundle(packets[r],**parts);encoded=bundle.encode();assert SceneBundle.decode(encoded)==bundle
 (target/f'{r}.nsb').write_bytes(encoded);checks.append(dict(refresh=r,bytes=len(encoded),objects=len(list(chunks(bundle.objects,'objects'))),supplements=len(list(chunks(bundle.supplements,'supplements')))))
r=dict(result='PASS_CAMERA_ALIGNED_SCENE_BUNDLES',scenes=len(checks),checks=checks,excluded_graphs=sorted(set(packets)-{x['refresh'] for x in checks}),scope='Owned graph/material/raw object/callback/supplement components; ordinary model assets and live publication incomplete.')
(p/'owned-scene-bundles.json').write_text(json.dumps(r,indent=2));print(r)
