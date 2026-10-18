import ctypes as C,json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
class Attributes(C.Structure):_fields_=[('count',C.c_uint32),('shift',C.c_uint32),('height',C.c_uint32),('affine',C.c_uint32),('material',C.c_uint32),('animation',C.c_uint32),('offsets',C.c_int32*2),('uv',(C.c_int32*2)*32)]
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=(C.c_uint32*32768).from_buffer_copy(Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nf_road_source_decode.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p];d.nf_road_camera_continuous.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p];d.nf_road_source_ring.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];d.nf_road_camera_ring.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];projection=(C.c_int32*3)(120,87,128);checks=[]
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());matrix=(C.c_int32*12).from_buffer_copy(c.graph.context[256:304]);tested=0
 for source in road_candidates(c,ClosedSceneMemory(c,rom)):
  n=len(source.vertices)//68;mat=bytearray(48);struct.pack_into('<HH',mat,36,struct.unpack_from('<H',source.material,26)[0],struct.unpack_from('<H',source.material,10)[0])
  for affine in (0,1):
   world=(C.c_double*96)();raw=Attributes();assert d.nf_road_source_decode(source.vertices,len(source.vertices),source.offsets,len(source.offsets),source.face,bytes(mat),n,affine,world,C.byref(raw))
   camera=(C.c_double*96)()
   for i in range(n):assert d.nf_road_camera_continuous(C.byref(world,i*24),matrix,C.byref(camera,i*24))
   a=(C.c_double*320)();b=(C.c_double*320)();na=C.c_uint();nb=C.c_uint();ok=d.nf_road_source_ring(world,n,C.byref(raw),matrix,projection,table,a,64,C.byref(na));same=d.nf_road_camera_ring(camera,n,C.byref(raw),projection,table,b,64,C.byref(nb));assert ok==same
   if ok:assert na.value==nb.value and list(a)[:na.value*5]==list(b)[:nb.value*5]
   camera[0]=float('nan');nb.value=123;b[0]=456
   assert not d.nf_road_camera_ring(camera,n,C.byref(raw),projection,table,b,64,C.byref(nb)) and nb.value==123 and b[0]==456
   tested+=1
 checks.append(dict(refresh=c.refresh,rings=tested))
out=dict(result='PASS_CAMERA_SPACE_ROAD_RING',checks=checks,scope='Exact endpoint source-ring equivalence including affine modes; camera correction and sampled submission still pending')
Path('work/camera/camera-space-road-ring-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],sum(x['rings'] for x in checks))
