from pathlib import Path
from dataclasses import replace
import struct,json
from owned_model_scene_packet import ModelScenePacket
p=Path('work/camera');meshes=b''
for file in sorted((p/'model-assets').glob('*.nma')):
 raw=file.read_bytes();meshes+=struct.pack('<I',len(raw))+raw
out=p/'model-scene-packets';out.mkdir(exist_ok=True);checks=[];rejected=0
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 packet=ModelScenePacket.compact(file.read_bytes(),(p/'owned-object-poses.bin').read_bytes(),(p/'owned-object-textures.bin').read_bytes(),(p/'owned-object-palettes.bin').read_bytes(),meshes)
 assert len(packet.poses)==292 and len(packet.palettes)==756 and len(packet.textures)==51748
 raw=packet.encode();loaded=ModelScenePacket.decode(raw);assert loaded==packet and loaded.gpu_records()==packet.gpu_records()
 (out/(file.stem+'.nsc')).write_bytes(raw);checks.append(dict(scene=file.name,bytes=len(raw)))
 for bad in (raw[:-1],bytes([raw[0]^1])+raw[1:]):
  try:ModelScenePacket.decode(bad)
  except ValueError:rejected+=1
  else:raise AssertionError('Bad packet accepted')
 for field in ('poses','textures','palettes','meshes'):
  try:replace(packet,**{field:b''}).encode()
  except ValueError:rejected+=1
  else:raise AssertionError('Missing model data accepted')
 wrong=bytearray(packet.poses);wrong[196]^=1
 try:replace(packet,poses=bytes(wrong)).encode()
 except ValueError:rejected+=1
 else:raise AssertionError('Foreign camera accepted')
assert len(checks)==7 and rejected==49
r=dict(result='PASS_IMMUTABLE_MODEL_SCENE_PACKET',checks=checks,invalid_packets_rejected=rejected,scope='Unified diagnostic publication unit; Scene-local companions and selected meshes only; live producer integration pending.')
(p/'owned-model-scene-packet.json').write_text(json.dumps(r,indent=2));print(r)
