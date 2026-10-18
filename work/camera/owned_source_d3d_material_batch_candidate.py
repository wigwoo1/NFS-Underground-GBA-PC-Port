"""Consume source-owned API packets directly; no GL command stream reads."""
import ctypes as C,numpy as np,hashlib,time
from pathlib import Path
class OwnedD3DConsumer:
 def __init__(self):
  self.vertex_bytes=C.create_string_buffer(65536*80);self.vertex_float=np.empty((65536,10),np.float32);self.offset_scratch=(C.c_uint*4097)();self.texture_scratch=C.create_string_buffer(16*1024*1024);self.texture_records=(C.c_uint*256)();self.texture_ids=(C.c_uint*4096)();self.state_scratch=C.create_string_buffer(4096*72);self.hud_batch_scratch=C.create_string_buffer(160*112)
  self.pixel_scratch=C.create_string_buffer(153600);self.backdrop_scratch=C.create_string_buffer(640);self.quad_cache={}
  self.texture_cache={};self.texture_cache_bytes=0;self.texture_uploads=0;self.texture_reuses=0
  p=Path(__file__).parent;self.d=C.CDLL(str((p/'owned-d3d-material-batch-candidate.dll').resolve()));d=self.d;P=C.c_void_p
  d.nf_d3d_texture.argtypes=[C.c_uint]*3+[P,C.c_size_t];d.nf_d3d_draw.argtypes=[P,C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,P];d.nf_d3d_hud_draw.argtypes=[P,C.c_uint,P,P,P,P];d.nf_d3d_clear.argtypes=[P];d.nf_d3d_read.argtypes=[P,C.c_size_t];d.nf_d3d_hud_shader.argtypes=[P,C.c_size_t]
  d.nf_d3d_texture_cached.argtypes=[C.c_uint]*3+[P,C.c_size_t];d.nf_d3d_material_packet_cached.argtypes=[P,C.c_size_t,P,C.c_uint,C.c_size_t];d.nf_d3d_texture_cache_stats.argtypes=[P];self.native_cache_stats=(C.c_uint64*3)()
  assert d.nf_d3d_open()==0
  code=(p/'owned-d3d-hud-effect-candidate.cso').read_bytes();assert d.nf_d3d_hud_shader(code,len(code))==0
 def upload_texture(self,identity,w,h,pixels,n):
  assert self.d.nf_d3d_texture_cached(identity,w,h,pixels,n)==0
 def bind_window(self):
  self.user=C.WinDLL('user32',use_last_error=True);u=self.user;P=C.c_void_p
  u.CreateWindowExW.argtypes=[C.c_uint,C.c_wchar_p,C.c_wchar_p,C.c_uint,C.c_int,C.c_int,C.c_int,C.c_int,P,P,P,P];u.CreateWindowExW.restype=P;u.DestroyWindow.argtypes=[P];u.ShowWindow.argtypes=[P,C.c_int]
  self.window=u.CreateWindowExW(0,'STATIC','NFS Underground - Native D3D Experiment',0x00cf0000,100,100,960,540,None,None,None,None);assert self.window
  u.ShowWindow(self.window,5);self.d.nf_d3d_window.argtypes=[P];self.d.nf_d3d_window_pump.argtypes=[P,P];assert self.d.nf_d3d_window(self.window)==0
 def present(self):
  state=(C.c_uint64*7)();assert self.d.nf_d3d_window_pump(self.window,state)==0
  status=self.d.nf_d3d_present();assert status in (0,3);return dict(status=status,window=list(state))
 def close(self):
  try:assert self.d.nf_d3d_close()==0;assert self.d.nf_d3d_present()==1
  finally:
   self.vertex_bytes=self.vertex_float=self.offset_scratch=self.texture_scratch=self.texture_records=self.texture_ids=self.state_scratch=self.hud_batch_scratch=None
   self.quad_cache.clear();self.pixel_scratch=None;self.backdrop_scratch=None
   self.texture_cache.clear();self.texture_cache_bytes=0
   if getattr(self,'window',None):assert self.user.DestroyWindow(self.window);self.window=None
 def render(self,s,readback=True):
  ticks=[time.perf_counter_ns()];self.stage_profile=[]
  def stage(name):
   now=time.perf_counter_ns();self.stage_profile.append(dict(stage=name,elapsed_ns=now-ticks[-1]));ticks.append(now)
  d=self.d;P=C.c_void_p;stats=(C.c_uint*3)();s.nf_source_packets_stats(stats);nv,nd,_=stats
  assert nv<=65536 and nd<=4096;vb=self.vertex_bytes;offsets=self.offset_scratch;assert s.nf_source_packets_copy(vb,nv*80,offsets,(nd+1)*4)==0;vertices=self.vertex_float[:nv];np.copyto(vertices,np.frombuffer(vb,np.float64,count=nv*10).reshape(nv,10),casting="unsafe")
  ts=(C.c_uint*2)();s.nf_source_texture_stats(ts);nt,nb=ts;assert nt<=64 and nb<=16*1024*1024;tb=self.texture_scratch;tr=self.texture_records;ids=self.texture_ids;assert s.nf_source_texture_copy(tb,nb,tr,nt*16,ids,nd*4)==0
  assert d.nf_d3d_material_packet_cached(tb,nb,tr,nt,nt*16)==0
  stage('material_copy_upload')
  states=self.state_scratch;assert s.nf_source_state_copy(states,nd*72)==0
  assert d.nf_d3d_clear((C.c_float*4)(.035,.05,.08,1))==0
  def quad(w,h,alpha):
   key=(w,h)
   if key not in self.quad_cache:
    assert key in ((240,1),(240,160),(3840,2160))
    self.quad_cache[key]=np.asarray([[x,y,u,v,0,1,1,1,1,alpha] for x,y,u,v in [(0,0,0,0),(w,0,1,0),(0,h,0,1),(w,0,1,0),(w,h,1,1),(0,h,0,1)]],np.float32)
   self.quad_cache[key][:,9]=alpha
   return self.quad_cache[key]
  backdrop_count=s.nf_source_backdrop_count();assert backdrop_count in (0,160)
  if backdrop_count:
   rows=self.backdrop_scratch;s.nf_source_backdrop_copy.argtypes=[P,C.c_size_t];assert s.nf_source_backdrop_copy(rows,640)==0
   colors=np.frombuffer(rows,np.uint8).reshape(160,4)
   config=(C.c_float*8)(0,240,160,0,0,0,0,0);rect=(C.c_int*8)(0,0,3840,2160,300,0,3240,2160)
   starts=np.concatenate(([0],np.flatnonzero(np.any(colors[1:]!=colors[:-1],axis=1))+1))
   ends=np.concatenate((starts[1:],[160]))
   template=quad(240,1,1)
   vertices_backdrop=np.repeat(template[None,:,:],len(starts),axis=0)
   vertices_backdrop[:,:,1]=template[None,:,1]*(ends-starts)[:,None]+starts[:,None]
   vertices_backdrop[:,:,6:10]=colors[starts,None,:].astype(np.float32)/255
   vertices_backdrop=vertices_backdrop.reshape(-1,10)
   assert d.nf_d3d_draw(vertices_backdrop.ctypes.data,len(vertices_backdrop),0,0,0,config,rect)==0
  stage('backdrop_geometry')
  skyvalid=(C.c_uint*2)();weights=(C.c_double*2)();s.nf_source_sky_info(skyvalid,weights)
  for i in range(2):
   if not skyvalid[i]:continue
   sky=self.pixel_scratch;assert s.nf_source_sky_copy(i,sky,len(sky))==0;self.upload_texture(1001+i,240,160,sky,len(sky))
   v=quad(240,160,weights[i]);config=(C.c_float*8)(0,240,160,0,1,int(i==0),.5,0);rect=(C.c_int*8)(0,0,3840,2160,300,0,3240,2160);assert d.nf_d3d_draw(v.ctypes.data,6,1001+i,3,i,config,rect)==0
  stage('sky_upload_draw')
  d.nf_d3d_world_batch.argtypes=[P,C.c_uint,C.c_size_t,P,C.c_size_t,P,C.c_size_t,P,C.c_uint,C.c_size_t]
  assert d.nf_d3d_world_batch(vertices.ctypes.data,nv,vertices.nbytes,offsets,(nd+1)*4,ids,nd*4,states,nd,nd*72)==0
  stage('world_geometry')
  hudinfo=(C.c_uint*2)();assert s.nf_source_hud_planes_info(hudinfo)==0
  if hudinfo[0]:
   assert d.nf_d3d_copy_target(1004)==0
   for i in range(3):
    plane=self.pixel_scratch;assert s.nf_source_hud_plane_copy(i,plane,len(plane))==0;self.upload_texture(1010+i,240,160,plane,len(plane))
   n=s.nf_source_hud_batches_count();assert n<=160;batch=self.hud_batch_scratch;assert s.nf_source_hud_batches_copy(batch,n*112)==0
   v=quad(3840,2160,1);config=(C.c_float*8)(0,3840,2160,0,0,0,0,0);textureids=(C.c_uint*4)(1010,1011,1004,1012)
   d.nf_d3d_hud_batch.argtypes=[P,C.c_uint,P,P,C.c_uint,C.c_size_t,P]
   assert d.nf_d3d_hud_batch(v.ctypes.data,6,textureids,batch,n,n*112,config)==0
  stage('background_copy_hud_upload_draw')
  assert d.nf_d3d_texture_cache_stats(self.native_cache_stats)==0
  self.texture_uploads,self.texture_reuses,self.texture_cache_bytes=list(self.native_cache_stats)
  if not readback:return None
  out=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(out,len(out))==0;return np.frombuffer(out,np.uint8).reshape(2160,3840,4)[:,:,:3].copy()
