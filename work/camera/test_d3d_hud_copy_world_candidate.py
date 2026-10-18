"""Actual captured source-world/sky D3D component. HUD deliberately pending."""
import ctypes as C,json,zlib,hashlib,threading
from pathlib import Path
import numpy as np
p=Path('work/camera');run=p/'prototype-runs';packet=json.loads((run/'normalized-source-gpu-packets.json').read_text());payload=(run/'source-command-state-payload.bin').read_bytes()
d=C.CDLL(str((p/'owned-d3d-hud-copy-candidate.dll').resolve()));P=C.c_void_p;d.nf_d3d_compile_error.restype=C.c_char_p
status=d.nf_d3d_open();assert status==0,(status,d.nf_d3d_compile_error())
d.nf_d3d_texture.argtypes=[C.c_uint]*3+[P,C.c_size_t];d.nf_d3d_draw.argtypes=[P,C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,P];d.nf_d3d_clear.argtypes=[P];d.nf_d3d_read.argtypes=[P,C.c_size_t];d.nf_d3d_stats.argtypes=[P]
foreign=[];t=threading.Thread(target=lambda:foreign.append(d.nf_d3d_clear((C.c_float*4)(0,0,0,0))));t.start();t.join();assert foreign==[1]
textures={};frames=[];skipped_hud=0;rgb=C.create_string_buffer(3840*2160*4)
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
  elif kind=='clear':assert d.nf_d3d_clear((C.c_float*4)(*op['color']))==0
  elif kind=='draw_triangles':
   if op['program']:skipped_hud+=1;continue
   state=op['state'];enabled=state['enabled'];tex=op['textures'].get('0');textured=0x0de1 in enabled
   tid=tex['resource'][0] if textured else 0;sampler=tex['sampler'] if tex else {};mode=int(sampler.get('10242',0x2901)==0x2901)+2*int(sampler.get('10243',0x2901)==0x2901)
   vertices=np.asarray([op['vertices'][i] for i in op['indices']],dtype=np.float32)
   config=(C.c_float*8)(*op['projection'][:4],float(textured),float(0x0bc0 in enabled),state['alpha'][1],0)
   if 0x0c11 in enabled:x,y,w,h=state['scissor'];rect=(C.c_int*8)(x,2160-y-h,x+w,2160-y,*state["viewport"])
   else:rect=(C.c_int*8)(0,0,3840,2160,*state["viewport"])
   assert d.nf_d3d_draw(vertices.ctypes.data,len(vertices),tid,mode,int(0x0be2 in enabled),config,rect)==0
  elif kind=='end_frame':
   assert d.nf_d3d_read(rgb,len(rgb))==0;image=np.frombuffer(rgb.raw,dtype=np.uint8).reshape(2160,3840,4)[:,:,:3].copy();ref=np.frombuffer(zlib.decompress((run/('gl-source-world-'+str(op['identity'][2])+'.rgb.z')).read_bytes()),dtype=np.uint8).reshape(2160,3840,3)
   different=np.any(image!=ref,axis=2);delta=np.abs(image.astype(np.int16)-ref.astype(np.int16));frames.append(dict(identity=op['identity'],different_pixels=int(different.sum()),maximum_channel_difference=int(delta.max()),rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(),reference_sha256=hashlib.sha256(ref.tobytes()).hexdigest()));(run/('d3d-hud-copy-world-'+str(op['identity'][2])+'.rgb.z')).write_bytes(zlib.compress(image.tobytes()))
 assert len(frames)==5 and skipped_hud==180
finally:
 stats=(C.c_uint64*4)();assert d.nf_d3d_stats(stats)==0;before=list(stats);assert d.nf_d3d_close()==0;assert d.nf_d3d_stats(stats)==0 and stats[2]==stats[3]==0
r=dict(result='PASS_D3D_SOURCE_WORLD_EXECUTION' if all(x['different_pixels']==0 for x in frames) else 'D3D_SOURCE_WORLD_PIXEL_PARITY_INCOMPLETE',frames=frames,stats_before_close=before,stats_after_close=list(stats),skipped_hud_draws=skipped_hud,foreign_thread_rejected=True,scope='Source-world/sky component only; full-scene HUD, live presentation, 60fps, physical4K and Xbox not verified. Native GPU draws, diagnostic readback only.')
(run/'d3d-hud-copy-world-component.json').write_text(json.dumps(r,indent=2));print(r)

