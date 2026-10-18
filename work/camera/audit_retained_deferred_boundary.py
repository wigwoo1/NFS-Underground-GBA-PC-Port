import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
folder=Path('G:\\EXTRA DATA DRIVE\\Desktop\\Games\\Codex\\NFSUG-Native-PC-Port\\work\\camera\\prototype-runs\\fullscene-failure-1791307723926901700')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())

from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_sampled_graph_wall_visibility import selected_graph_walls,wall_metadata
from owned_closed_scene_memory import ClosedSceneMemory
portal=PortalMotionPair(*(s.graph.graph for s in scenes),table,PreparedMotionPair(*frames,*scenes))
checks=[]
for i in range(101):
 alpha=i/100;rows=[]
 try:selected=selected_graph_walls(portal,alpha)
 except ValueError as error:
  checks.append(dict(alpha=alpha,deferred=[],error=str(error)));continue
 for candidate,visibility in selected:
  if visibility.flags&2:
   desc,ring,offsets=wall_metadata(portal,portal.newer if alpha==1 else portal.older)[0][candidate.descriptor]
   count=len(ring)//68;bit=1<<(count-candidate.edge)
   rows.append(dict(descriptor=candidate.descriptor,ordinal=candidate.ordinal,edge=candidate.edge,ring_count=count,mask_bit=bit,retained_mask_bit=bit&255,flags=visibility.flags,bounds=candidate.bounds))
 checks.append(dict(alpha=alpha,deferred=rows))

Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
class Action(C.Structure):_fields_=[('kind',C.c_uint32),('pass_number',C.c_uint32),('mask',C.c_uint32),('record',C.c_uint8*16)]
d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nfs_visibility_region_actions.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
ct=(C.c_uint32*32768)(*table);endpoint_actions=[]
for endpoint,scene in enumerate(scenes):
 memory=ClosedSceneMemory(scene.graph,rom)
 @Reader
 def read(ctx,address,out,size):
  try:C.memmove(out,memory.read(address,size),size);return 1
  except ValueError:return 0
 for region in portal.sample(endpoint):
  if region[0] not in (86,87) or region[5]&8:continue
  output=(Action*515)();count=C.c_uint()
  assert d.nfs_visibility_region_actions(scene.graph.graph.context[:256],struct.pack('<8H',*region,65535),0,read,None,ct,output,515,C.byref(count))
  actions=[dict(kind=x.kind,mask=x.mask) for x in output[:count.value]]
  endpoint_actions.append(dict(endpoint=endpoint,descriptor=region[0],actions=actions,missing_reads=memory.missing))
result=dict(result='DEFERRED_BOUNDARY_SOURCE_AUDIT',older=scenes[0].graph.refresh,newer=scenes[1].graph.refresh,checks=checks,endpoint_actions=endpoint_actions,scope='Source-owned fractional wall flags and original low-eight-bit deferred mask; actual command/raster parity unverified')
Path('work/camera/retained-deferred-boundary-audit.json').write_text(json.dumps(result,indent=2))
print(dict(older=result['older'],newer=result['newer'],deferred_samples=sum(bool(x['deferred']) for x in checks),other_failures=[(x['alpha'],x['error']) for x in checks if 'error' in x],unique_edges=sorted({(r['descriptor'],r['edge'],r['ring_count'],r['retained_mask_bit']) for x in checks for r in x['deferred']})))
