import ctypes as C,struct,json
from pathlib import Path
setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0]
exec(compile(setup,'native-draw-setup','exec'))
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class Draw(C.Structure):
 _fields_=[('frame',P),('bytes',C.c_size_t),('camera',P),('models',P),('bounds',P),('count',C.c_uint),('lower',P),('upper',P),('skycount',C.c_size_t),('weight',C.c_double),('result',C.c_int),('started_ns',U),('completed_ns',U),('thread_cycles',U)]
class Present(C.Structure):_fields_=[('epoch',U),('timed',C.c_uint32),('result',C.c_int32),('elapsed_ns',U)]
gpu=C.CDLL(str(Path('work/camera/owned-sky-gpu.dll').resolve()));h=C.CDLL(str(Path('work/camera/owned-draw-commit-candidate.dll').resolve()))
gpu.nf_owned_gpu_draw_context_size.restype=C.c_size_t;assert gpu.nf_owned_gpu_draw_context_size()==C.sizeof(Draw)
gpu.nf_owned_gpu_draw.argtypes=[P,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[P,C.c_size_t,P,P,P,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
h.nf_owned_handoff_create.argtypes=[U];h.nf_owned_handoff_create.restype=P;h.nf_owned_handoff_destroy.argtypes=[P]
f=h.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
draw= C.cast(gpu.nf_owned_gpu_draw_context_callback,CB);present=C.cast(gpu.nf_owned_gpu_present_callback,CB)
q=None;checks=[];rgb=C.create_string_buffer(3840*2160*3)
try:
 assert gpu.nf_owned_gpu_window(0)==0
 for index,alpha in enumerate((0,.5,1)):
  frame,cam,models,bounds,detail=prepared.sample(alpha);buf=C.create_string_buffer(frame);epoch=struct.unpack_from('<Q',frame,24)[0]
  if q is None:q=h.nf_owned_handoff_create(epoch)
  assert (gpu.nf_owned_gpu_draw(buf,len(frame)) if alpha in (0,1) else gpu.nf_owned_gpu_draw_scene_clips(buf,len(frame),cam,models,bounds,detail['geometry_records']))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  ctx=Draw(C.cast(buf,P),len(frame),C.cast(cam,P),C.cast(models,P),None if alpha in (0,1) else C.cast(bounds,P),detail['geometry_records'],None,None,0,0,-999,0,0,0)
  pc=Present(epoch,1,-999,0);sample=(U*8)();wait=(U*4)();stages=(U*7)()
  assert f(q,epoch,1,scenes[0].identity[1],scenes[1].identity[1],index,alpha,0,draw,C.byref(ctx),present,C.byref(pc),sample,wait,stages)==1
  assert ctx.result==pc.result==0 and ctx.started_ns<=ctx.completed_ns<=sample[6] and ctx.thread_cycles!=2**64-1
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  checks.append(dict(alpha=alpha,full_4k_rgb_exact=True,draw_ns=ctx.completed_ns-ctx.started_ns,cycles=ctx.thread_cycles))
finally:
 if q:h.nf_owned_handoff_destroy(q)
 assert gpu.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-draw-context-20261007')
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',context_size=C.sizeof(Draw),checks=checks,scope='Actual complete sampled scene GPU/native draw+commit direct function pointers and exact4K readbacks; sky payload and live cadence integration pending'),indent=2))
print('PASS direct native draw and present',checks)
