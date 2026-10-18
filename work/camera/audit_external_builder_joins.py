"""Recover external rotation from exact original builder inputs and compare consumed poses."""
import sys,json,struct
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_projection import signed,multiply
report=json.loads(Path(sys.argv[1]).read_text());p=Path(report['model_pose_trace']);store=OwnedModelBuilders(p.with_suffix('.builders.bin').read_bytes());raw=p.with_suffix('.builders.bin.external.bin').read_bytes();assert len(raw)%64==0
external={}
for at in range(0,len(raw),64):
 h=struct.unpack_from('<7I',raw,at);assert h[0]==0x31584d4e and h[6]==1
 external[(h[1],h[2],h[3])]=(h[4],h[5],raw[at+28:at+64])
checks=[];poses=p.read_bytes();assert len(poses)%292==0
for at in range(0,len(poses),292):
 h=struct.unpack_from('<8I',poses,at);obj=poses[at+32:at+196]
 if not struct.unpack_from('<H',obj,10)[0]&32:continue
 builder=store.at(h[3],h[5],h[1]);special,address,data=external[(builder.refresh,builder.object_address,builder.matrix_address)]
 assert special and address==struct.unpack_from('<I',builder.source,140)[0]
 camera=struct.unpack('<12i',builder.camera);rotation=multiply(tuple(signed(x<<2) for x in struct.unpack('<9i',data)),camera[:9])
 px,py,pz=struct.unpack_from('<3i',builder.source,12);x=signed((px>>8)+camera[9]);z=signed((pz>>8)+camera[11])
 translation=(signed(camera[0]*x+camera[6]*z)>>14,signed((py>>8)+camera[10]),signed(camera[2]*x+camera[8]*z)>>14)
 actual=struct.pack('<12i',*(rotation+translation));assert actual==poses[at+244:at+292],('External pose mismatch',h[1],h[3])
 checks.append(dict(refresh=h[1],source=h[3],builder_refresh=builder.refresh,matrix=h[5],exact=True))
assert checks,'No external consumed pose checked'
p.with_suffix('.external-joins.json').write_text(json.dumps(dict(external_inputs=len(external),checks=checks),indent=2))
print('PASS original external rotation reconstruction equals consumed poses:',len(checks),'checks from',len(external),'input records')
