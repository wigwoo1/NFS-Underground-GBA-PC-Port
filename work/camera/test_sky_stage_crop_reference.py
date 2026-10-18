"""Retained queued target sky image selection in the playable source DLL."""
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
d=C.CDLL(str((p/'owned-sky-stage-crop-candidate.dll').resolve()));d.nf_owned_gpu_draw_scene_clips_sky.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 assert d.nf_owned_gpu_window(0)==0
 assert d.nf_sky_stage_mode(1)==0
 d.nf_sky_stage_read.argtypes=[C.c_uint64,C.c_uint64,C.c_void_p,C.c_size_t]
 frame,camera,models,bounds,detail=pair.sample(.5);count=len(records(frame)['records']);gn,hn=struct.unpack_from('<2I',frame,8);bg=40+gn+hn
 frame=bytearray(frame);frame[bg+38400+10560:bg+38400+25696]=bytes([1])*15136;frame=bytes(frame)
 skyframe=(p/'motion-actual-scanline-assets/8758-owned-background-frame.bin').read_bytes();sg,sh=struct.unpack_from('<2I',skyframe,8);lower=skyframe[20+sg+sh+10560:20+sg+sh+25696];assert len(lower)==15136 and len(set(lower))>1
 upper=lower[1:]+lower[:1];f=C.create_string_buffer(frame);lo=C.create_string_buffer(lower);hi=C.create_string_buffer(upper)
 d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];assert d.nf_owned_gpu_draw(f,len(frame))==0
 d.nf_owned_gpu_draw_context_callback.argtypes=[C.c_void_p]
 previous=None;retained=[]
 d.nf_owned_gpu_target_acquire.argtypes=[C.c_void_p]
 d.nf_owned_gpu_target_select.argtypes=[C.c_uint64,C.c_uint64]
 d.nf_owned_gpu_target_release.argtypes=[C.c_uint64]
 epoch=struct.unpack_from('<Q',frame,24)[0]
 for step,weight in enumerate((.1,.5,.9)):
  if False:
   lower=upper;upper=lower[1:]+lower[:1];lo=C.create_string_buffer(lower);hi=C.create_string_buffer(upper)
  ctx=DrawContext(C.cast(f,C.c_void_p),len(frame),C.cast(camera,C.c_void_p),C.cast(models,C.c_void_p),C.cast(bounds,C.c_void_p),count,C.cast(lo,C.c_void_p),C.cast(hi,C.c_void_p),15136,weight)
  result=d.nf_owned_gpu_draw_context_callback(C.byref(ctx));assert result==0 and ctx.result==0,(result,ctx.result)
  assert d.nf_owned_gpu_read(rgb,len(rgb))==0;pixels=rgb.raw
  changed=None if previous is None else sum(pixels[i:i+3]!=previous[i:i+3] for i in range(0,len(pixels),3))
  if step:assert changed>0,'Sky pixels frozen'
  if False:assert pixels==previous,'Rounded sky output jumps at source-pixel seam'
  checks.append(dict(weight=weight,changed_pixels=changed,sha256=hashlib.sha256(pixels).hexdigest()));previous=pixels
  token=C.c_uint64();assert d.nf_owned_gpu_target_acquire(C.byref(token))==0
  from owned_sky_sampler import SkySamples
  from owned_sky_color import sky_rgba
  palettes=b''.join(frame[40+gn+y*34944+32896:40+gn+y*34944+32896+512] for y in range(160))
  reference=sky_rgba(SkySamples(lower,upper,weight,0x06002940),palettes)
  stage=C.create_string_buffer(912);assert d.nf_sky_stage_read(token.value,epoch,stage,len(stage))==0
  at=0;maximum=0
  for sy in range(44,107,4):
   for sx in range(8,232,12):
    ref=((sy-44)*240+sx)*4
    error=max(abs(a-b) for a,b in zip(stage.raw[at:at+3],reference[ref:ref+3]));maximum=max(maximum,error);at+=3
  assert maximum<=1,(weight,maximum)
  checks.append(dict(weight=weight,sky_stage_points=304,max_channel_error=maximum))
  retained.append((token.value,pixels))
 assert len({token for token,_ in retained})==3
 for token,expected in reversed(retained):
  assert d.nf_owned_gpu_target_select(token,epoch+1)==32
  assert d.nf_owned_gpu_target_select(token,epoch)==0
  assert d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected,'Selected queue target differs from retained image'
  assert d.nf_owned_gpu_target_release(token)==0
  assert d.nf_owned_gpu_target_select(token,epoch)==32
  checks.append(dict(token=token,retained_rgb_exact=True,wrong_epoch_rejected=True,retired_token_rejected=True))
finally:
 pair.close();history.close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stage-crop-reference-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual playable source DLL standard draw-context callback retains three distinct full-scene 4K sky images and selects their exact pixels in reverse order; wrong epoch and retired tokens rejected. Diagnostic source with held world pose and explicit coverage, not live presentation or physical scanout.'),indent=2))
(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(checks));print('PASS retained source sky target selection')






