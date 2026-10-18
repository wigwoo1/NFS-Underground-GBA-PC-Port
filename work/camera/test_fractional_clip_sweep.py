"""Actual production full-scene callback pixels at varying sky weights."""
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
d=C.CDLL(str((p/'owned-sky-fractional-clip-candidate.dll').resolve()));d.nf_owned_gpu_draw_scene_clips_sky.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 frame,camera,models,bounds,detail=pair.sample(.5);count=len(records(frame)['records']);gn,hn=struct.unpack_from('<2I',frame,8);bg=40+gn+hn
 frame=bytearray(frame);frame[bg+38400+10560:bg+38400+25696]=bytes([1])*15136;frame=bytes(frame)
 skyframe=(p/'motion-actual-scanline-assets/8758-owned-background-frame.bin').read_bytes();sg,sh=struct.unpack_from('<2I',skyframe,8);lower=skyframe[20+sg+sh+10560:20+sg+sh+25696];assert len(lower)==15136 and len(set(lower))>1
 upper=lower[1:]+lower[:1];f=C.create_string_buffer(frame);lo=C.create_string_buffer(lower);hi=C.create_string_buffer(upper)
 d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];assert d.nf_owned_gpu_draw(f,len(frame))==0
 previous=None
 for weight in (0,):
  ctx=DrawContext(C.cast(f,C.c_void_p),len(frame),C.cast(camera,C.c_void_p),C.cast(models,C.c_void_p),C.cast(bounds,C.c_void_p),count,C.cast(lo,C.c_void_p),C.cast(hi,C.c_void_p),15136,weight)
  result=d.nf_owned_gpu_draw_scene_clips_sky(ctx.frame,ctx.bytes,ctx.camera,ctx.models,ctx.bounds,ctx.count,ctx.lower,ctx.upper,ctx.skycount,ctx.weight);assert result==0,result
  assert d.nf_owned_gpu_read(rgb,len(rgb))==0;pixels=rgb.raw
  changed=None if previous is None else sum(pixels[i:i+3]!=previous[i:i+3] for i in range(0,len(pixels),3))
  if previous is not None:assert changed>0,'Production fullscene sky callback pixels frozen'
  checks.append(dict(weight=weight,changed_pixels=changed,sha256=hashlib.sha256(pixels).hexdigest()));previous=pixels
 motion_checks=[]
 import math
 from PIL import Image,ImageChops
 transitions=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/fractional-visibility-transitions-20261007/transitions.json').read_text())['transitions'];added={tuple(k) for t in transitions for k in t['added'] if k[0]==1}
 for alpha in (.598,.599,.600,.602,.604,.606,.608,.610):
  frame,camera,models,bounds,detail=pair.sample(alpha);rr=records(frame)['records'];count=len(rr);indices=[i for i,row in enumerate(rr) if row['key'] in added];assert len(indices)==4
  gn,hn=struct.unpack_from('<2I',frame,8);bg=40+gn+hn;frame=bytearray(frame);frame[bg+38400+10560:bg+38400+25696]=bytes([1])*15136;f=C.create_string_buffer(bytes(frame))
  blocked=(C.c_double*len(bounds))(*bounds)
  intervals=[]
  for i in indices:
   left,right,top,bottom=list(bounds[i*4:i*4+4]);blocked[i*4+1]=left
   end=right+min(1,max(0,right-left));x0=300+math.ceil(left*13.5-.5);x1=300+math.ceil(end*13.5-.5);intervals.append((x0,x1))
  images=[]
  for clipbounds in (bounds,blocked):
   assert d.nf_owned_gpu_draw_scene_clips_sky(f,len(frame),camera,models,clipbounds,count,lo,hi,15136,.5)==0
   assert d.nf_owned_gpu_read(rgb,len(rgb))==0;images.append(Image.frombytes('RGB',(3840,2160),rgb.raw))
  diff=ImageChops.difference(*images);bbox=diff.getbbox();xmin=min(x[0] for x in intervals);xmax=max(x[1] for x in intervals)
  if bbox:assert xmin<=bbox[0]<bbox[2]<=xmax,'Opening roads write outside fragment-center clip'
  motion_checks.append(dict(alpha=alpha,native_clip_columns=[xmin,xmax],difference_bbox=bbox,coverage_width=xmax-xmin))
 assert all(b['coverage_width']>=a['coverage_width'] for a,b in zip(motion_checks,motion_checks[1:]))
finally:
 pair.close();history.close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/fractional-clip-sweep-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',geometry_records=count,checks=checks,motion_checks=motion_checks,scope='Default corrected queued GPU full-scene function: fixed .5 motion and varying diagnostic sky, then varying .2/.4/.6/.8 scene motion with fixed diagnostic sky. Explicit sky coverage attachment; outer input/present callback excluded. Pixel-change component proof, not independent visual correctness or physical scanout.'),indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(motion_checks));print('PASS production fullscene sky draw')
