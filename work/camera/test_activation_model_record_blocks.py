"""Complete generated model blocks match original active endpoints."""
import runpy,struct
from pathlib import Path
from owned_model_assets import model_record_blocks,model_palette_equivalent
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_projection import SceneryProjection
from owned_ordinary_model_visits import ordinary_model_visits
from owned_closed_scene_memory import ClosedSceneMemory
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_activation_model_assets.py');fixture=v['v'];scene=v['scenes'][1];rom=v['rom'];memory=ClosedSceneMemory(scene,rom)
store=OwnedModelBuilders((fixture['folder']/'newer.builders.bin').read_bytes());projection=SceneryProjection(rom)
visits={x['object']:x for x in ordinary_model_visits(scene,fixture['portal'].sample(1))};rows=[r for r in records(fixture['frames'][1])['records'] if r['kind']==3]
base=struct.unpack_from('<I',scene.graph.context,60)[0];matrix_base=struct.unpack_from('<I',scene.graph.context,252)[0];exact=0;rebuilt_by_descriptor={}
for item in v['results'][1]['items']:
 visit=visits[item['object']];builder=store.at(base+item['object']*164,matrix_base+visit['source'][136]*48,scene.refresh)
 matrix=projection.matrix(builder.camera,builder.source,builder.initial_matrix)
 blocks=model_record_blocks(struct.pack('<17I',*item['context']),memory,matrix,scene.graph.context[304:368],visit['bounds'],scene.graph.context[384:896])
 offset=item['descriptor']-0x08000000;matches=[r for r in rows if bytes(r['blocks'][1])==rom[offset:offset+40]];assert len(matches)==1
 rebuilt_by_descriptor[bytes(blocks[1])]=blocks
 original=matches[0]['blocks']
 assert all(blocks[i]==bytes(original[i]) for i in range(11)),item['object']
 assert model_palette_equivalent(blocks,bytes(original[11]))
 exact+=sum(blocks[i]==bytes(original[i]) for i in range(12))
 # A change to a used palette entry must fail even if other entries agree.
 changed=bytearray(original[11]);index=next(iter(set(blocks[10])));changed[index*2]^=1
 assert not model_palette_equivalent(blocks,bytes(changed))
assert exact==56
print('PASS: 56/60 byte-exact model blocks; remaining four palettes differ only at unused index0; used colour mutation rejected')
