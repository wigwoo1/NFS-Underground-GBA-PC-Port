import ctypes as C,json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_endpoint_road_selection import endpoint_road_span_candidates
from owned_sampled_road_clip import Attributes,clipped_camera_road
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);table=(C.c_uint32*32768)(*reciprocal);d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nf_road_source_decode.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p];d.nf_road_camera_continuous.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p];d.nf_road_scratch_create.restype=C.c_void_p;d.nf_road_scratch_destroy.argtypes=[C.c_void_p];d.nf_road_source_clipped.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];scratch=d.nf_road_scratch_create();branch=d.nf_road_scratch_create();checks=[]
try:
 for f in r['wall_diagnostic_frames']:
  c=ClosedGraph.decode(Path(f['graph']).read_bytes());m=ClosedSceneMemory(c,rom);state=c.graph.context[:256];base=struct.unpack_from('<I',state,108)[0];matrix=(C.c_int32*12).from_buffer_copy(c.graph.context[256:304]);tested=0;fractional=0;count_differences=0
  for item in endpoint_road_span_candidates(c,m,road_candidates(c,m),reciprocal,include_empty=True):
   x=item['source'];n=len(x.vertices)//68;mat=bytearray(48);struct.pack_into('<HH',mat,36,struct.unpack_from('<H',x.material,26)[0],struct.unpack_from('<H',x.material,10)[0]);world=(C.c_double*96)();attrs=Attributes();assert d.nf_road_source_decode(x.vertices,len(x.vertices),x.offsets,len(x.offsets),x.face,bytes(mat),n,item['affine'],world,C.byref(attrs));camera=(C.c_double*(n*3))()
   for i in range(n):assert d.nf_road_camera_continuous(C.byref(world,i*24),matrix,C.byref(camera,i*24))
   projected=clipped_camera_road(d,branch,camera,attrs,item['bounds'],base,item['input_count'],table,commit_branch=True)
   if item['bounds'][0]+.25<item['bounds'][1]:
    bounds=list(item['bounds']);bounds[0]+=.25;clipped_camera_road(d,scratch,camera,attrs,bounds,base,item['input_count'],table);fractional+=1
   out=(C.c_double*768)();amount=C.c_uint();missing=C.c_uint64();bounds=(C.c_uint16*4)(*item['bounds'])
   assert d.nf_road_source_clipped(scratch,x.vertices,len(x.vertices),x.offsets,len(x.offsets),x.face,bytes(mat),n,item['affine'],matrix,bounds,base,item['input_count'],table,out,128,C.byref(amount),C.byref(missing))
   assert projected['count']==amount.value and projected['missing']==missing.value and projected['ring']==tuple(out)[:amount.value*6]
   count_differences+=projected['projected_count']!=item['input_count'];tested+=1
  checks.append(dict(refresh=c.refresh,endpoint_clips_exact=tested,fractional_clip_samples=fractional,projected_count_differs_from_stream=count_differences))
finally:d.nf_road_scratch_destroy(branch);d.nf_road_scratch_destroy(scratch)
out=dict(result='PASS_SEQUENTIAL_CAMERA_ROAD_BRANCH',checks=checks,scope='Camera ring/depth/fractional horizontal clipping pipeline on one presentation branch across all surfaces and scenes; endpoint stream counts supplied, continuous stream count still pending')
Path('work/camera/sequential-camera-road-branch-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],sum(x['endpoint_clips_exact'] for x in checks),sum(x['fractional_clip_samples'] for x in checks),sum(x['projected_count_differs_from_stream'] for x in checks))
