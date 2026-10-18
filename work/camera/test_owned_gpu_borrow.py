from pathlib import Path
import ctypes as C,json,hashlib
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_borrowed_frames.restype=C.c_uint64
frame=(p/'motion-actual-scanline-assets/8766-native-complete-frame.bin').read_bytes();owned=C.create_string_buffer(frame,len(frame));before=owned.raw
try:
 assert d.nf_owned_gpu_draw(owned,len(owned))==0;assert owned.raw==before;assert d.nf_owned_gpu_borrowed_frames()==1
 # Caller can retire or reuse its packet after the synchronous API returns.
 C.memset(owned,0,len(owned));assert d.nf_owned_gpu_finish()==0
 rgb=C.create_string_buffer(3840*2160*3);assert d.nf_owned_gpu_read(rgb,len(rgb))==0
 assert rgb.raw==(p/'owned-timed-8766.ppm').read_bytes().split(b'\n',3)[3]
finally:assert d.nf_owned_gpu_close()
r=dict(result='PASS_GPU_IMMUTABLE_PACKET_BORROW',borrowed_frame_bytes=len(frame),caller_packet_unchanged_during_draw=True,caller_reuse_after_return_safe=True,completed_endpoint_exact=True,scope='Synchronous immutable packet ownership and rendered image only; does not eliminate HUD/texture copies or prove60fps.')
(p/'owned-gpu-borrow-tests.json').write_text(json.dumps(r,indent=2));print(r)
