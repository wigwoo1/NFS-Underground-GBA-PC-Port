import ctypes as C,json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_wall_region_candidates import regions
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);ct=(C.c_uint32*32768)(*table);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
class Action(C.Structure):_fields_=[('kind',C.c_uint32),('pass_number',C.c_uint32),('mask',C.c_uint32),('record',C.c_uint8*16)]
d.nfs_visibility_region_actions.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());memory=ClosedSceneMemory(c,rom)
 @Reader
 def read(ctx,address,out,size):
  try:C.memmove(out,memory.read(address,size),size);return 1
  except ValueError:return 0
 actions=[];failed=[];queue=regions(c.graph,table)
 for pass_number in (0,1):
  for ordinal,region in reversed(list(enumerate(queue))):
   if region[5]&(0x88 if pass_number else 8):continue
   record=struct.pack('<8H',*region,65535) if len(region)==7 else struct.pack('<8H',*region)
   output=(Action*515)();count=C.c_uint();ok=d.nfs_visibility_region_actions(c.graph.context[:256],record,pass_number,read,None,ct,output,515,C.byref(count))
   if not ok:failed.append(dict(ordinal=ordinal,descriptor=region[0],pass_number=pass_number));continue
   actions.extend(dict(ordinal=ordinal,descriptor=struct.unpack_from('<H',bytes(a.record))[0],kind=a.kind,pass_number=a.pass_number,mask=a.mask) for a in output[:count.value])
 checks.append(dict(refresh=c.refresh,actions=actions,failed=failed,missing_reads=sorted(set(memory.missing))))
assert len(checks)==16 and all(not x['failed'] and not x['missing_reads'] for x in checks)
out=dict(result='PASS_CLOSED_SCENE_REGION_ACTION_OWNERSHIP',checks=checks,scope='Owned read closure for native region action ordering; missing dependencies explicitly recorded, recursive command assembly not yet integrated.')
Path('work/camera/closed-scene-region-action-audit.json').write_text(json.dumps(out,indent=2));print([(x['refresh'],len(x['actions']),len(x['failed']),x['missing_reads'][:3]) for x in checks])
