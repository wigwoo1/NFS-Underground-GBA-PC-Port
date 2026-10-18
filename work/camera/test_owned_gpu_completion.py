from pathlib import Path
import ctypes as C,threading,json
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
assert d.nf_owned_gpu_window(0)==0;assert d.nf_owned_gpu_finish()==32
try:
 frame=(p/'motion-actual-scanline-assets/8766-native-complete-frame.bin').read_bytes();assert d.nf_owned_gpu_draw(frame,len(frame))==0;assert d.nf_owned_gpu_finish()==0
 rgb=C.create_string_buffer(3840*2160*3);assert d.nf_owned_gpu_read(rgb,len(rgb))==0;assert rgb.raw==(p/'owned-timed-8766.ppm').read_bytes().split(b'\n',3)[3]
 wrong=[];t=threading.Thread(target=lambda:wrong.append(d.nf_owned_gpu_finish()));t.start();t.join();assert wrong==[31]
finally:assert d.nf_owned_gpu_close()
r=dict(result='PASS_GPU_COMPLETION_BARRIER_COMPONENT',no_frame_rejected=True,wrong_thread_rejected=True,completed_endpoint_image_exact=True,scope='Completion barrier component only, no scanout/fullscene60fps proof.')
(p/'owned-gpu-completion-tests.json').write_text(json.dumps(r,indent=2));print(r)
