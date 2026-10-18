"""Diagnostic native/caller timing; graphics call order retained."""
import ctypes as C,time,inspect,textwrap
import owned_source_d3d_sky_pan_display_candidate as display
from owned_uncovered_window_candidate import OwnedD3DConsumer
import owned_packet_profile_install_candidate as packet
U64_4=C.c_uint64*4
method=display.OwnedD3DConsumer.__init__;source=textwrap.dedent(inspect.getsource(method));assert source.count('owned-d3d-sky-pan-display-candidate.dll')==1
source=source.replace('owned-d3d-sky-pan-display-candidate.dll','owned-d3d-call-profile-candidate.dll')
source=source.replace('assert d.nf_d3d_open()==0',"d.nf_d3d_material_packet_cached_profiled.argtypes=[P,C.c_size_t,P,C.c_uint,C.c_size_t,P,C.c_size_t]\n d.nf_d3d_world_batch_profiled.argtypes=[P,C.c_uint,C.c_size_t,P,C.c_size_t,P,C.c_size_t,P,C.c_uint,C.c_size_t,P,C.c_size_t]\n d.nf_d3d_source_hud_batch_profiled.argtypes=[P]*5+[C.c_size_t]\n assert d.nf_d3d_open()==0")
ns=dict(method.__globals__);exec(compile(source,'d3d-call-init','exec'),ns);display.OwnedD3DConsumer.__init__=ns['__init__']
def profiled(self,name,args):
 if not hasattr(self,'draw_profile_buffer'):self.draw_profile_buffer=U64_4()
 begin=time.perf_counter_ns();result=getattr(self.d,name+'_profiled')(*args,self.draw_profile_buffer,32);end=time.perf_counter_ns();w0,w1,c0,c1=self.draw_profile_buffer
 self.d3d_call_profiles.append(dict(call=name,caller_begin_ns=begin,caller_end_ns=end,native_begin_ns=w0,native_end_ns=w1,native_cycles=c1-c0));return result
source=packet.source
source=source.replace('ticks=[time.perf_counter_ns()];self.stage_profile=[]','ticks=[time.perf_counter_ns()];self.stage_profile=[];self.d3d_call_profiles=[]')
for name,args in [('nf_d3d_material_packet_cached','tb,nb,tr,nt,nt*16'),('nf_d3d_world_batch','vertices.ctypes.data,nv,vertices.nbytes,offsets,(nd+1)*4,ids,nd*4,states,nd,nd*72'),('nf_d3d_source_hud_batch','C.cast(s.nf_source_hud_planes_info,P),C.cast(s.nf_source_hud_plane_copy,P),C.cast(s.nf_source_hud_batches_count,P),C.cast(s.nf_source_hud_batches_copy,P)')]:
 old=f'd.{name}({args})';assert source.count(old)==1;source=source.replace(old,f'profiled(self,"{name}",({args},))')
ns=dict(OwnedD3DConsumer.render.__globals__);ns.update(profiled=profiled);exec(compile(source,'d3d-call-render','exec'),ns);OwnedD3DConsumer.render=ns['render']
