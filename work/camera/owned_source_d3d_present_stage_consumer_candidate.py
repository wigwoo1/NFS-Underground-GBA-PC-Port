"""Consume source-owned API packets directly; no GL command stream reads."""
import ctypes as C,numpy as np,hashlib,time
from pathlib import Path
class OwnedD3DConsumer:
 def __init__(self):
  self.texture_cache={};self.texture_cache_bytes=0;self.texture_uploads=0;self.texture_reuses=0
  p=Path(__file__).parent;self.d=C.CDLL(str((p/'owned-d3d-present-stage-candidate.dll').resolve()));d=self.d;P=C.c_void_p
  d.nf_d3d_texture.argtypes=[C.c_uint]*3+[P,C.c_size_t];d.nf_d3d_draw.argtypes=[P,C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,P];d.nf_d3d_hud_draw.argtypes=[P,C.c_uint,P,P,P,P];d.nf_d3d_clear.argtypes=[P];d.nf_d3d_read.argtypes=[P,C.c_size_t];d.nf_d3d_hud_shader.argtypes=[P,C.c_size_t]
  assert d.nf_d3d_open()==0
  code=(p/'owned-d3d-hud-effect-candidate.cso').read_bytes();assert d.nf_d3d_hud_shader(code,len(code))==0
 def upload_texture(self,identity,w,h,pixels,n):
  content=C.string_at(pixels,n);key=(w,h,content)
  if self.texture_cache.get(identity)==key:
   self.texture_reuses+=1;return
  assert self.d.nf_d3d_texture(identity,w,h,pixels,n)==0
  self.texture_uploads+=1
  old=self.texture_cache.pop(identity,None)
  if old is not None:self.texture_cache_bytes-=len(old[2])
  if self.texture_cache_bytes+n<=16*1024*1024:
   self.texture_cache[identity]=key;self.texture_cache_bytes+=n
 def bind_window(self):
  self.user=C.WinDLL('user32',use_last_error=True);u=self.user;P=C.c_void_p
  u.CreateWindowExW.argtypes=[C.c_uint,C.c_wchar_p,C.c_wchar_p,C.c_uint,C.c_int,C.c_int,C.c_int,C.c_int,P,P,P,P];u.CreateWindowExW.restype=P;u.DestroyWindow.argtypes=[P];u.ShowWindow.argtypes=[P,C.c_int]
  self.window=u.CreateWindowExW(0,'STATIC','NFSUG direct source native diagnostic',0x00cf0000,100,100,960,540,None,None,None,None);assert self.window
  u.ShowWindow(self.window,5);self.d.nf_d3d_window.argtypes=[P];self.d.nf_d3d_window_pump.argtypes=[P,P];assert self.d.nf_d3d_window(self.window)==0
 def present(self):
  state=(C.c_uint64*7)();begin=time.perf_counter_ns();assert self.d.nf_d3d_window_pump(self.window,state)==0
  pumped=time.perf_counter_ns();status=self.d.nf_d3d_present();ended=time.perf_counter_ns();profile=(C.c_uint64*9)();assert self.d.nf_d3d_present_profile(profile)==0;assert status in (0,3);return dict(native_c_profile=list(profile),status=status,window=list(state),native_present_timing=dict(begin_ns=begin,pumped_ns=pumped,ended_ns=ended))
 def close(self):
  try:assert self.d.nf_d3d_close()==0;assert self.d.nf_d3d_present()==1
  finally:
   self.texture_cache.clear();self.texture_cache_bytes=0
   if getattr(self,'window',None):assert self.user.DestroyWindow(self.window);self.window=None
 def render(self,s,readback=True):
  ticks=[time.perf_counter_ns()];self.stage_profile=[]
  def stage(name):
   now=time.perf_counter_ns();self.stage_profile.append(dict(stage=name,elapsed_ns=now-ticks[-1]));ticks.append(now)
  d=self.d;P=C.c_void_p;stats=(C.c_uint*3)();s.nf_source_packets_stats(stats);nv,nd,_=stats
  vb=C.create_string_buffer(nv*80);offsets=(C.c_uint*(nd+1))();assert s.nf_source_packets_copy(vb,len(vb),offsets,C.sizeof(offsets))==0;vertices=np.frombuffer(vb.raw,np.float64).reshape(nv,10).astype(np.float32)
  ts=(C.c_uint*2)();s.nf_source_texture_stats(ts);nt,nb=ts;tb=C.create_string_buffer(nb);tr=(C.c_uint*(nt*4))();ids=(C.c_uint*nd)();assert s.nf_source_texture_copy(tb,nb,tr,C.sizeof(tr),ids,C.sizeof(ids))==0
  for i in range(nt):w,h,start,n=tr[i*4:i*4+4];self.upload_texture(i+1,w,h,C.cast(C.byref(tb,start),P),n)
  stage('material_copy_upload')
  states=C.create_string_buffer(nd*72);assert s.nf_source_state_copy(states,len(states))==0
  assert d.nf_d3d_clear((C.c_float*4)(.035,.05,.08,1))==0
  def quad(w,h,alpha):
   return np.asarray([[x,y,u,v,0,1,1,1,1,alpha] for x,y,u,v in [(0,0,0,0),(w,0,1,0),(0,h,0,1),(w,0,1,0),(w,h,1,1),(0,h,0,1)]],np.float32)
  backdrop_count=s.nf_source_backdrop_count();assert backdrop_count in (0,160)
  if backdrop_count:
   rows=C.create_string_buffer(640);s.nf_source_backdrop_copy.argtypes=[P,C.c_size_t];assert s.nf_source_backdrop_copy(rows,640)==0
   colors=np.frombuffer(rows.raw,np.uint8).reshape(160,4)
   config=(C.c_float*8)(0,240,160,0,0,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,300,0,3240,2160)
   y=0
   while y<160:
    end=y+1
    while end<160 and np.array_equal(colors[end],colors[y]):end+=1
    v=quad(240,end-y,1);v[:,1]+=y;v[:,6:10]=colors[y].astype(np.float32)/255;assert d.nf_d3d_draw(v.ctypes.data,6,0,0,0,config,rect)==0;y=end
  stage('backdrop_geometry')
  skyvalid=(C.c_uint*2)();weights=(C.c_double*2)();s.nf_source_sky_info(skyvalid,weights)
  for i in range(2):
   if not skyvalid[i]:continue
   sky=C.create_string_buffer(153600);assert s.nf_source_sky_copy(i,sky,len(sky))==0;self.upload_texture(1001+i,240,160,sky,len(sky))
   v=quad(240,160,weights[i]);config=(C.c_float*8)(0,240,160,0,1,int(i==0),.5,0);rect=(C.c_int*8)(0,0,3840,2160,300,0,3240,2160);assert d.nf_d3d_draw(v.ctypes.data,6,1001+i,3,i,config,rect)==0
  stage('sky_upload_draw')
  for i in range(nd):
   import struct
   state=struct.unpack_from('<8f8i2I',states.raw,i*72);config=(C.c_float*8)(*state[:8]);rect=(C.c_int*8)(*state[8:16]);a,b=offsets[i:i+2];assert d.nf_d3d_draw(vertices[a:b].ctypes.data,b-a,ids[i],state[16],state[17],config,rect)==0
  stage('world_geometry')
  hudinfo=(C.c_uint*2)();assert s.nf_source_hud_planes_info(hudinfo)==0
  if hudinfo[0]:
   assert d.nf_d3d_copy_target(1004)==0
   for i in range(3):
    plane=C.create_string_buffer(153600);assert s.nf_source_hud_plane_copy(i,plane,len(plane))==0;self.upload_texture(1010+i,240,160,plane,len(plane))
   n=s.nf_source_hud_batches_count();batch=C.create_string_buffer(n*112);assert s.nf_source_hud_batches_copy(batch,len(batch))==0
   v=quad(3840,2160,1);config=(C.c_float*8)(0,3840,2160,0,0,0,0,0);textureids=(C.c_uint*4)(1010,1011,1004,1012)
   for i in range(n):
    import struct
    clip=struct.unpack_from('<4i',batch.raw,i*112+96);rect=(C.c_int*8)(*clip,0,0,3840,2160);assert d.nf_d3d_hud_draw(v.ctypes.data,6,textureids,C.byref(batch,i*112),config,rect)==0
  stage('background_copy_hud_upload_draw')
  if not readback:return None
  out=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(out,len(out))==0;return np.frombuffer(out.raw,np.uint8).reshape(2160,3840,4)[:,:,:3].copy()
