"""Retain original shared-car descriptors and external source builder evidence."""
import runpy,struct,json,hashlib
from pathlib import Path
from owned_motion_pairs import records
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scene_bundle import chunks
v=runpy.run_path('work/camera/audit_complete_model_transition.py');out=[]
for endpoint,(scene,frame) in enumerate(zip(v['scenes'],v['frames'])):
 models=[dict(index=i,context=r['context'],descriptor=bytes(r['blocks'][1]).hex(),pose=struct.unpack('<12i',r['blocks'][2]),bounds=bytes(r['blocks'][9]).hex(),fingerprint=hashlib.sha256(b''.join(r['blocks'])).hexdigest()) for i,r in enumerate(records(frame)['records']) if r['kind']==3]
 base=struct.unpack_from('<I',scene.graph.context,60)[0];builders=OwnedModelBuilders((v['folder']/(('older','newer')[endpoint]+'.builders.bin')).read_bytes());sources=[]
 for h,raw in chunks(scene.objects,'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168]
   if index==1:sources.append(dict(parent=h[3],source=index,model=struct.unpack_from('<h',source,54)[0],flags=struct.unpack_from('<2H',source,8),slot=source[136]))
 inputs=[dict(refresh=b.refresh,matrix_address=b.matrix_address,flags=struct.unpack_from('<2H',b.source,8),slot=b.source[136],camera=struct.unpack('<12i',b.camera),initial=struct.unpack('<12i',b.initial_matrix)) for (address,_),values in builders.records.items() if address==base+164 for b in values]
 out.append(dict(endpoint=endpoint,source_refresh=scene.graph.refresh,draws=models,opponent_chain=sources,opponent_builders=inputs))
assert len(out[0]['draws'])==1 and len(out[1]['draws'])==2
assert out[1]['draws'][0]['descriptor']==out[1]['draws'][1]['descriptor']
assert out[1]['draws'][0]['pose']!=out[1]['draws'][1]['pose']
assert out[1]['opponent_builders'] and out[1]['opponent_builders'][-1]['flags'][1]&32
(v['folder']/'shared-car-draws.json').write_text(json.dumps(out,indent=2))
print('PASS two distinct original car draws share descriptor; source1 external-matrix builder retained. Pose ownership still requires external matrix closure.')
