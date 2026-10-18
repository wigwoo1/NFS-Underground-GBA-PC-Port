"""Inspect source-owned builder availability across model slot activation."""
import json,struct,ctypes as C
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_scene_bundle import chunks
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_projection import SceneryProjection
from owned_motion_pairs import records as frame_records
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def read(_,address,target,n):
 offset=address-0x08000000
 if not 0<=offset<=len(rom)-n:return 0
 C.memmove(target,rom[offset:offset+n],n);return 1
projection=SceneryProjection(rom)
lib=C.CDLL('work/camera/visibility-probe-wide.dll');fn=lib.nf_object_projection_matrix;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p]
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791280093968732600.json').read_text());folder=Path(r['full_scene_failure_capture']['folder']);results=[]
for label in ('older','newer'):
 graph=GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes());state=graph.context[:256];base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0]
 builders=OwnedModelBuilders((folder/(label+'.builders.bin')).read_bytes());sources={}
 for h,raw in chunks((folder/(label+'.objects.bin')).read_bytes(),'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168];sources[index]=source
 model_rows=[r for r in frame_records((folder/(label+'.frame.bin')).read_bytes())['records'] if r['kind']==3]
 items=[]
 for index,source in sources.items():
  model=struct.unpack_from('<h',source,54)[0]
  if not 31<=model<=36:continue
  address=base+index*164;slot=source[136]
  records=[v for (obj,matrix),values in builders.records.items() if obj==address for v in values]
  exact=None
  if slot!=255:
   value=builders.at(address,matrix_base+slot*48,graph.refresh)
   output=C.create_string_buffer(value.initial_matrix,48);assert fn(value.camera,value.source,output,read,None)
   descriptor=struct.unpack_from('<I',state,124)[0]+(model-1)*40;offset=descriptor-0x08000000
   matches=[row for row in model_rows if bytes(row['blocks'][1])==rom[offset:offset+40]]
   assert len(matches)==1
   assert projection.matrix(value.camera,value.source,value.initial_matrix)==bytes(output)
   exact=bytes(output)==bytes(matches[0]['blocks'][2]);assert exact,'Live retained builder transform mismatch'
  items.append(dict(exact_consumed_matrix=exact,object=index,model=model,slot=slot,builder_count=len(records),builder_refreshes=[v.refresh for v in records],active_slot_owned=any(v.matrix_address==matrix_base+slot*48 for v in records) if slot!=255 else False,source_positions=[list(struct.unpack_from('<3i',v.source,12)) for v in records],current_position=list(struct.unpack_from('<3i',source,12))))
 results.append(dict(endpoint=label,refresh=graph.refresh,items=items))
(folder/'builder-activation.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

assert sum(item['exact_consumed_matrix'] is True for endpoint in results for item in endpoint['items'])==5
print('PASS: five live scene-owned activation transforms match consumed matrices exactly')
