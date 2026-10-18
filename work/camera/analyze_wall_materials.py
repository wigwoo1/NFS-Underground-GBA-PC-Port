"""Validate discrete wall material frame selection from retained state."""
from pathlib import Path
import struct,json,collections
from scene_batches import records
from surface_identity import wall_identity
root=Path('work/camera');count=0;sequences=collections.defaultdict(list);identities=collections.defaultdict(set)
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def w(b,o):return struct.unpack_from('<I',b,o)[0]
for e in records(root/'materials.bin'):
 if e['pc']!=0x03000304:continue
 b=e['blocks'];state=b[1][1];source=b[5][1];base_address,base=b[77];selection_address,selection=b[78]
 assert base_address==w(state,32)+u(source,44)*32
 assert selection_address==w(state,72)+u(base,0)*8
 frame=u(selection,2);assert b[4][0]==base_address+frame*32
 selected=b[4][1];mat=b[8][1]
 assert u(mat,36)==u(selected,26) and u(mat,38)==u(selected,10)
 assert w(mat,40)==(w(state,0)+w(selected,4))&0xffffffff
 key=(b[5][0],base_address,u(base,0))
 identities[key].add(wall_identity(e))
 sequence=sequences[key]
 if not sequence or sequence[-1]['material_frame']!=frame:sequence.append({'refresh':e['frame'],'material_frame':frame,'texture':hex(w(mat,40))})
 count+=1
assert count
assert all(len(values)==1 for values in identities.values())
changing=[{'source':hex(key[0]),'base_material':hex(key[1]),'animation_id':key[2],'changes':sequence} for key,sequence in sequences.items() if len(sequence)>1]
report={'result':'PASS','wall_draws':count,'stable_world_identities':len(identities),'changing_material_sequences':changing,'scope':'Original frame-index selection, texture address and dimensions. Animation clock update code and other materials remain to recover.'}
(root/'wall-material-tests.json').write_text(json.dumps(report,indent=2));print(report)
