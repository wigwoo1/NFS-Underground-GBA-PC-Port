"""Full4K framebuffer parity for separate versus combined native poll/draw."""
from pathlib import Path
import ctypes as C,struct,hashlib,json,threading
setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0];exec(compile(setup,'owned-fullscene-setup','exec'))
g=C.CDLL(str(Path('work/camera/owned-sky-gpu.dll').resolve()));P=C.c_void_p
args=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double]
g.nf_owned_gpu_draw_scene_clips_sky.argtypes=args;g.nf_owned_gpu_poll_draw_scene_clips_sky.argtypes=args;g.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
checks=[];out=C.create_string_buffer(3840*2160*3)
try:
 assert g.nf_owned_gpu_window(0)==0
 for alpha in (.25,.5,.75):
  frame,cm,models,bounds,detail=prepared.sample(alpha);raw=bytearray(frame);h=struct.unpack_from('<6I2Q',raw);bg=40+h[2]+h[3]
  lower=bytes(raw[bg+10560:bg+25696]);upper=lower[1:]+lower[:1];raw[bg+38400+10560:bg+38400+25696]=bytes([1])*15136;frame=bytes(raw)
  for fraction in (0,.375):
   call=(frame,len(frame),cm,models,bounds,detail['geometry_records'],lower,upper,15136,fraction)
   poll=g.nf_owned_input_poll();draw=g.nf_owned_gpu_draw_scene_clips_sky(*call);read=g.nf_owned_gpu_read(out,len(out));assert poll and draw==0 and read==0,(alpha,fraction,poll,draw,read);baseline=out.raw
   assert g.nf_owned_gpu_poll_draw_scene_clips_sky(*call)==0 and g.nf_owned_gpu_read(out,len(out))==0 and out.raw==baseline
   checks.append({'alpha':alpha,'fraction':fraction,'framebuffer_sha256':hashlib.sha256(baseline).hexdigest()})
  rejected=[];t=threading.Thread(target=lambda:rejected.append(g.nf_owned_gpu_poll_draw_scene_clips_sky(*call)));t.start();t.join(5);assert rejected==[31] and not t.is_alive()
finally:assert g.nf_owned_gpu_close();prepared.close();history.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-input-draw-batch-20261006');(cp/'tests.json').write_text(json.dumps({'result':'PASS','checks':checks,'scope':'Actual captured complete world motion geometry/HUD at.25/.5/.75, indexed sky endpoint/fraction, all4Kpixels exact separate/batched native APIs; foreign owner rejection. No physical controller or live cadence proof'},indent=2));print('PASS native input/draw full4K parity',len(checks),'samples')
