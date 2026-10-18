"""Queued complete-scene sky continuity across a source-pixel boundary."""
import ctypes as C,json,struct,hashlib
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_pairs import records
from live_native_batch_candidate import DrawContext
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());fa,fb=r['wall_diagnostic_frames'][:2]
a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);roads,_=history.plan(a);pair=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,roads,rom)
d=C.CDLL(str((p/'owned-sky-source-context-candidate.dll').resolve()));d.nf_owned_gpu_draw_scene_clips_sky.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 frame,camera,models,bounds,detail=pair.sample(.5);count=len(records(frame)['records']);gn,hn=struct.unpack_from('<2I',frame,8);bg=40+gn+hn
 frame=bytearray(frame);frame[bg+38400+10560:bg+38400+25696]=bytes([1])*15136;frame=bytes(frame)
 skyframe=(p/'motion-actual-scanline-assets/8758-owned-background-frame.bin').read_bytes();sg,sh=struct.unpack_from('<2I',skyframe,8);lower=skyframe[20+sg+sh+10560:20+sg+sh+25696];assert len(lower)==15136 and len(set(lower))>1
 upper=lower[1:]+lower[:1];f=C.create_string_buffer(frame);lo=C.create_string_buffer(lower);hi=C.create_string_buffer(upper)
 d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];assert d.nf_owned_gpu_draw(f,len(frame))==0
 previous=None
 for step,weight in enumerate((.98,.999999,0,.02)):
  if step==2:
   lower=upper;upper=lower[1:]+lower[:1];lo=C.create_string_buffer(lower);hi=C.create_string_buffer(upper)
  ctx=DrawContext(C.cast(f,C.c_void_p),len(frame),C.cast(camera,C.c_void_p),C.cast(models,C.c_void_p),C.cast(bounds,C.c_void_p),count,C.cast(lo,C.c_void_p),C.cast(hi,C.c_void_p),15136,weight)
  result=d.nf_owned_gpu_draw_scene_clips_sky(ctx.frame,ctx.bytes,ctx.camera,ctx.models,ctx.bounds,ctx.count,ctx.lower,ctx.upper,ctx.skycount,ctx.weight);assert result==0,result
  assert d.nf_owned_gpu_read(rgb,len(rgb))==0;pixels=rgb.raw
  changed=None if previous is None else sum(pixels[i:i+3]!=previous[i:i+3] for i in range(0,len(pixels),3))
  if step in (1,3):assert changed>0,'Sky pixels frozen on moving side of seam'
  if step==2:assert pixels==previous,'Rounded sky output jumps at source-pixel seam'
  checks.append(dict(weight=weight,changed_pixels=changed,sha256=hashlib.sha256(pixels).hexdigest()));previous=pixels
finally:
 pair.close();history.close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-context-sky-pixel-seam-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual playable source-context GPU complete-scene callback readbacks, held world pose and cyclic diagnostic sky source. Adjacent source-pixel seam rounds to identical 4K output; moving samples on both sides change. Coverage explicitly attached. Not a live presentation capture or physical scanout test.'),indent=2))
(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(checks));print('PASS queued sky pixel seam')

