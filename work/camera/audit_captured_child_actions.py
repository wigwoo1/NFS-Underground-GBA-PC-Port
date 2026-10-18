import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_complete_supplemental_gpu import endpoint_gpu_records
from owned_live_wall_adapter import reconstruct
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791276350925813100.json').read_text());folder=Path(report['full_scene_failure_capture']['folder']);scenes=[];supp=[];frames=[]
for label in ('older','newer'):
 frame=(folder/(label+'.frame.bin')).read_bytes();frames.append(frame);scene=ClosedGraph(struct.unpack_from('<Q',frame,24)[0],struct.unpack_from('<I',frame,4)[0],GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes()),*( (folder/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(scene);supp.append(ClosedSupplements.decode((folder/(label+'.supplements.bin')).read_bytes(),scene))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(*(s.graph for s in scenes),table,PreparedMotionPair(*frames));pair=CompleteSupplementalCandidates(*scenes,*supp,portal,rom)

from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates

Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
class Action(C.Structure):_fields_=[('kind',C.c_uint32),('pass_number',C.c_uint32),('mask',C.c_uint32),('record',C.c_uint8*16)]
d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nfs_visibility_region_actions.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
ct=(C.c_uint32*32768)(*table);scene=scenes[1];memory=ClosedSceneMemory(scene,rom)
@Reader
def read(ctx,address,out,size):
 try:C.memmove(out,memory.read(address,size),size);return 1
 except ValueError:return 0
roots=[q for q in portal.sample(1) if q[0]==26 and not q[5]&8];assert roots
trace=[]
def walk(record,stack=()):
 identifier=struct.unpack_from('<H',record)[0]
 if identifier in stack:raise ValueError('Recursive source cycle')
 out=(Action*515)();n=C.c_uint();ok=d.nfs_visibility_region_actions(scene.graph.context[:256],record,0,read,None,ct,out,515,C.byref(n))
 if not ok:trace.append(dict(parent=identifier,failed=True));return
 for a in out[:n.value]:
  item=dict(parent=identifier,kind=a.kind,descriptor=struct.unpack_from('<H',bytes(a.record))[0],record=list(struct.unpack('<8H',bytes(a.record))))
  trace.append(item)
  if a.kind==2:walk(bytes(a.record),stack+(identifier,))
for q in roots:walk(struct.pack('<8H',*q,65535))

result=dict(result='CAPTURED_RECURSIVE_ACTION_CLOSURE_AUDIT',trace=trace,missing_reads=memory.missing,scope='Original integer endpoint region actions and recursive order; fractional transforms and GPU pixels unverified.')
(folder/'recursive-child-actions.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))



