"""Retained world, walls and car through production packet/model GPU consumer."""
from pathlib import Path
import csv,ctypes as C,json,hashlib,sys,struct,os
import numpy as np
from PIL import Image
p=Path('work/camera').resolve()
hud_enabled='--hud' in sys.argv
continuous_uv='--continuous-uv' in sys.argv
source_prefix=os.environ.get('NF_REPLAY_SOURCE_PREFIX','road-attribute-motion');packet_prefix=os.environ.get('NF_REPLAY_PACKET_PREFIX','visibility-transition');report_prefix=os.environ.get('NF_REPLAY_REPORT_PREFIX')
hud_invalid_rejections=0
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
sources=list(csv.DictReader((p/(source_prefix+'-sources.csv')).open()))
poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/(source_prefix+'-cameras.csv')).open())}
d=C.CDLL(str(p/'road-transition-gpu-probe.dll'));d.nf_road_transition_gpu_init.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p];d.nf_scene_transition_gpu_render.argtypes=[C.c_void_p,C.c_double,C.c_int,C.c_void_p,C.c_void_p]
rgb=np.empty((2160,3840,3),np.uint8);depth=np.empty((2160,3840),np.float32);records=[];contacts=[]
for i,source in enumerate(sources):
 packet=(p/f'{packet_prefix}-{i:03}.packet').read_bytes();owned=C.create_string_buffer(packet)
 assert d.nf_road_transition_gpu_init(owned,len(packet),str(p/'road-correction-reciprocal.bin').encode())==0
 try:
  hud_owned=None
  if hud_enabled:
   hud=(p/f'{packet_prefix}-{i:03}.hud').read_bytes();magic,row_size,rows,refresh,epoch,target=struct.unpack_from('<4IQd',hud)
   assert magic==0x3148464e and row_size==34944 and rows==160 and len(hud)==32+rows*row_size
   assert refresh==int(source['hud_refresh']) and epoch==int(source['epoch']) and abs(target-float(source['target']))<1e-10
   hud_owned=C.create_string_buffer(hud);d.nf_scene_transition_gpu_hud.argtypes=[C.c_void_p,C.c_size_t];assert d.nf_scene_transition_gpu_hud(hud_owned,len(hud))
   assert not d.nf_scene_transition_gpu_hud(hud_owned,len(hud)-1);hud_invalid_rejections+=1
   for offset,fmt,value in [(0,'I',0),(4,'I',1),(16,'Q',0),(32,'I',refresh+1),(32+159*row_size+4,'I',160)]:
    bad=bytearray(hud);struct.pack_into('<'+fmt,bad,offset,value);bad_owned=C.create_string_buffer(bytes(bad));assert not d.nf_scene_transition_gpu_hud(bad_owned,len(bad));hud_invalid_rejections+=1
  assert d.nf_road_transition_gpu_uv_mode(2 if continuous_uv or not hud_enabled else 0)
  camera=(Pose*2)(poses[i,0],poses[i,1]);native=(Pose*2)();assert d.nf_road_transition_gpu_native_camera(native)
  alpha=float(source['alpha']);captured=C.c_double();assert d.nf_road_transition_gpu_capture_alpha(C.byref(captured)) and abs(alpha-captured.value)<1e-10
  images=[];masks=[]
  draw_counts=None
  for pair,a,bounds in [(camera,alpha,1),(camera,alpha,0),(native,0,1)]:
   before=(C.c_uint64*4)();after=(C.c_uint64*4)();assert d.nf_scene_transition_gpu_counters(before)
   result=d.nf_scene_transition_gpu_render(pair,a,bounds,rgb.ctypes.data,depth.ctypes.data);assert result==0,(i,result)
   assert d.nf_scene_transition_gpu_counters(after)
   if draw_counts is None:
    draw_counts=[b-a for a,b in zip(before,after)];assert all(n>0 for n in draw_counts[:3]),(i,draw_counts)
   assert np.isfinite(depth).all() and np.count_nonzero(depth)>0
   images.append(rgb.copy());masks.append(depth>0)
  records.append(dict(index=i,target=float(source['target']),bounded_pixels=int(masks[0].sum()),unbounded_pixels=int(masks[1].sum()),removed_pixels=int((masks[1]&~masks[0]).sum()),added_pixels=int((masks[0]&~masks[1]).sum()),camera_changed_rgb=int(np.any(images[0]!=images[2],axis=2).sum()),camera_changed_coverage=int(np.count_nonzero(masks[0]!=masks[2])),image_sha256=hashlib.sha256(images[0].tobytes()).hexdigest()))
  records[-1]['bounded_render_draw_counts']=dict(zip(['roads','classified_wall_batches','models','lighting_fallback'],draw_counts))
  if hud_enabled:
   reference=np.asarray(Image.open(p/f'{source_prefix}-{i:03}.ppm'))[::-1]
   records[-1]['live_frame_changed_pixels']=int(np.any(reference!=images[0],axis=2).sum())
  if i in (0,4,9,11):contacts.append(np.asarray(Image.fromarray(images[0][::-1]).resize((960,540))))
 finally:d.nf_road_transition_gpu_close()
Image.fromarray(np.concatenate(contacts,axis=0)).save(p/((report_prefix+'-contact.png') if report_prefix else 'full-scene-transition-contact.png'))
report=dict(result='PASS',rendered_4K_cases=36,packets=12,records=records,hardware_hud=hud_enabled,continuous_near_uv=continuous_uv,exact_live_frames=sum(r.get('live_frame_changed_pixels',-1)==0 for r in records),scope='Actual production geometry consumer with retained native order/bounds and optional scanline-owned HUD through live compositor. Explicit selected near-UV policy must match the live capture. Native capture replay parity, not original GBA raster parity or whole-route smooth60fps proof.')
report['invalid_hud_rejections']=hud_invalid_rejections
if hud_enabled and report['exact_live_frames']!=12:report['result']='FAIL'
(p/((report_prefix+'-hud-replay-tests.json') if report_prefix else 'full-scene-hud-replay-tests.json' if hud_enabled else 'full-scene-transition-gpu-tests.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if hud_enabled:assert report['exact_live_frames']==12, 'Retained replay differs from live complete frames'
