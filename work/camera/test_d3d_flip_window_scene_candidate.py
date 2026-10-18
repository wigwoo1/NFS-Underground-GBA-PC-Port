"""Full-scene flip-model D3D component; sandbox presentation is not scanout proof."""
import ctypes as C,json,zlib,hashlib,threading
from pathlib import Path
import numpy as np
p=Path('work/camera');run=p/'prototype-runs';packet=json.loads((run/'normalized-source-gpu-packets.json').read_text());payload=(run/'source-command-state-payload.bin').read_bytes()
d=C.CDLL(str((p/'owned-d3d-flip-window-candidate.dll').resolve()));P=C.c_void_p;d.nf_d3d_compile_error.restype=C.c_char_p
user=C.WinDLL('user32',use_last_error=True);user.CreateWindowExW.argtypes=[C.c_uint,C.c_wchar_p,C.c_wchar_p,C.c_uint,C.c_int,C.c_int,C.c_int,C.c_int,P,P,P,P];user.CreateWindowExW.restype=P;user.DestroyWindow.argtypes=[P];user.ShowWindow.argtypes=[P,C.c_int];window=user.CreateWindowExW(0,'STATIC','NFSUG native D3D scene diagnostic',0x00cf0000,100,100,960,540,None,None,None,None);assert window;user.ShowWindow(window,5)
status=d.nf_d3d_open();assert status==0,(status,d.nf_d3d_compile_error())
d.nf_d3d_texture.argtypes=[C.c_uint]*3+[P,C.c_size_t];d.nf_d3d_draw.argtypes=[P,C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,P];d.nf_d3d_clear.argtypes=[P];d.nf_d3d_read.argtypes=[P,C.c_size_t];d.nf_d3d_stats.argtypes=[P]
foreign=[];t=threading.Thread(target=lambda:foreign.append(d.nf_d3d_clear((C.c_float*4)(0,0,0,0))));t.start();t.join();assert foreign==[1]
d.nf_d3d_hud_shader.argtypes=[P,C.c_size_t];d.nf_d3d_hud_draw.argtypes=[P,C.c_uint,P,P,P,P];code=(p/'owned-d3d-hud-effect-candidate.cso').read_bytes();assert d.nf_d3d_hud_shader(code,len(code))==0
d.nf_d3d_window.argtypes=[P];assert d.nf_d3d_window(window)==0;assert d.nf_d3d_window(window)==1;foreign_present=[];t=threading.Thread(target=lambda:foreign_present.append(d.nf_d3d_present()));t.start();t.join();assert foreign_present==[1]
telemetry=[];d.nf_d3d_window_pump.argtypes=[P,P];present_results=[];textures={};frames=[];skipped_hud=0;rgb=C.create_string_buffer(3840*2160*4)
try:
 for op in packet['ops']:
  kind=op['op']
  if kind in ('allocate_texture','update_texture'):
   if not op['payload_bytes']:continue
   a=list(map(int,op['args']));raw=payload[op['payload_offset']:op['payload_offset']+op['payload_bytes']];tid=op['target'][0]
   if kind=='allocate_texture':w,h=a[3:5];textures[tid]=np.frombuffer(raw,dtype=np.uint8).reshape(h,w,4).copy()
   else:
    x,y,w,h=a[2:6];textures[tid][y:y+h,x:x+w]=np.frombuffer(raw,dtype=np.uint8).reshape(h,w,4)
   image=textures[tid];assert d.nf_d3d_texture(tid,image.shape[1],image.shape[0],image.ctypes.data,image.nbytes)==0
  elif kind=='copy_render_target':
   assert list(map(int,op['args']))==[3553,0,0,0,0,0,3840,2160];assert d.nf_d3d_copy_target(op['target'][0])==0
  elif kind=='clear':assert d.nf_d3d_clear((C.c_float*4)(*op['color']))==0
  elif kind=='draw_triangles':
   state=op['state'];enabled=state['enabled'];tex=op['textures'].get('0');textured=0x0de1 in enabled
   tid=tex['resource'][0] if textured else 0;sampler=tex['sampler'] if tex else {};mode=int(sampler.get('10242',0x2901)==0x2901)+2*int(sampler.get('10243',0x2901)==0x2901)
   vertices=np.asarray([op['vertices'][i] for i in op['indices']],dtype=np.float32)
   config=(C.c_float*8)(*op['projection'][:4],float(textured),float(0x0bc0 in enabled),state['alpha'][1],0)
   if 0x0c11 in enabled:x,y,w,h=state['scissor'];rect=(C.c_int*8)(x,2160-y-h,x+w,2160-y,*state["viewport"])
   else:rect=(C.c_int*8)(0,0,3840,2160,*state["viewport"])
   if op['program']:
    u=op['uniforms'];ids=(C.c_uint*4)(*[op['textures'][str(int(u[n][0]))]['resource'][0] for n in ('candidateColor','candidateMetadata','nativeBackground','ownedText')]);values=[]
    for n in ('backdropColor','effectParameters','firstTargets','secondTargets','coefficients'):values.extend(u[n])
    import struct
    params=C.create_string_buffer(struct.pack('<20fi3f',*values,int(u['ownedTextEnabled'][0]),0,0,0));config[4]=0
    assert d.nf_d3d_hud_draw(vertices.ctypes.data,len(vertices),ids,params,config,rect)==0;skipped_hud+=1
   else:assert d.nf_d3d_draw(vertices.ctypes.data,len(vertices),tid,mode,int(0x0be2 in enabled),config,rect)==0
  elif kind=='end_frame':
   window_state=(C.c_uint64*7)();assert d.nf_d3d_window_pump(window,window_state)==0;telemetry.append(list(window_state));present_status=d.nf_d3d_present();present_results.append(present_status);assert present_status in (0,3),present_status
   assert d.nf_d3d_read(rgb,len(rgb))==0;image=np.frombuffer(rgb.raw,dtype=np.uint8).reshape(2160,3840,4)[:,:,:3].copy();ref=np.frombuffer(zlib.decompress((run/('gl-source-full-'+str(op['identity'][2])+'.rgb.z')).read_bytes()),dtype=np.uint8).reshape(2160,3840,3)
   different=np.any(image!=ref,axis=2);delta=np.abs(image.astype(np.int16)-ref.astype(np.int16));frames.append(dict(identity=op['identity'],different_pixels=int(different.sum()),maximum_channel_difference=int(delta.max()),rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(),reference_sha256=hashlib.sha256(ref.tobytes()).hexdigest()));(run/('d3d-flip-window-scene-'+str(op['identity'][2])+'.rgb.z')).write_bytes(zlib.compress(image.tobytes()))
 assert len(frames)==5 and skipped_hud==180
finally:
 stats=(C.c_uint64*4)();assert d.nf_d3d_stats(stats)==0;before=list(stats);assert d.nf_d3d_close()==0;assert d.nf_d3d_present()==1;assert d.nf_d3d_stats(stats)==0 and stats[2]==stats[3]==0
user.DestroyWindow(window)
r=dict(window_telemetry=telemetry,presentation_results=present_results,result='PASS_D3D_SOURCE_WORLD_EXECUTION' if all(x['different_pixels']==0 for x in frames) else 'D3D_FULL_SCENE_PIXEL_PARITY_INCOMPLETE',frames=frames,stats_before_close=before,stats_after_close=list(stats),executed_hud_draws=skipped_hud,foreign_thread_rejected=True,scope='Full-scene offscreen component including HUD; live presentation, 60fps, physical4K and Xbox not verified. Native GPU draws, diagnostic readback only.')
(run/'d3d-flip-window-scene-component.json').write_text(json.dumps(r,indent=2));print(r)



