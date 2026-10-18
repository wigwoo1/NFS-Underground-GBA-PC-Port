"""Experimental single-call packet transfer; exact conversion and D3D order retained."""
import ctypes as C,ast,inspect,textwrap
from pathlib import Path
import owned_native_source_hud_cache_lease_session_candidate as hud
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_renderer_fixed_types_install_candidate import U32_3,U32_2,F32_4
method=hud.NativeSourceSession.__init__;source=textwrap.dedent(inspect.getsource(method));assert source.count('owned-gpu-source-hud-cache-lease-candidate.dll')==1
source=source.replace('owned-gpu-source-hud-cache-lease-candidate.dll','owned-gpu-source-packet-profile-candidate.dll')
source=source.replace('configure_hud_library(self.source)',"configure_hud_library(self.source)\n self.source.nf_source_packet_bundle_profiled.argtypes=[C.c_void_p,C.c_size_t]*8")
ns=dict(method.__globals__);exec(compile(source,'packet-bundle-session','exec'),ns);hud.NativeSourceSession.__init__=ns['__init__']
source=Path(__file__).with_name('owned_source_d3d_sky_pan_candidate.py').read_text();tree=ast.parse(source);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef));method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='render');source=textwrap.dedent(ast.get_source_segment(source,method))
start=source.index('  d=self.d;P=C.c_void_p;stats=');end=source.index('  assert d.nf_d3d_material_packet_cached',start)
source=source[:start]+"""  d=self.d;P=C.c_void_p;vb=self.vertex_bytes;offsets=self.offset_scratch;tb=self.texture_scratch;tr=self.texture_records;ids=self.texture_ids;states=self.state_scratch
  if not hasattr(self,'bundle_metadata'):self.bundle_metadata=(C.c_uint*5)()
  stats=self.bundle_metadata
  if not hasattr(self,"bundle_timings"):self.bundle_timings=(C.c_uint64*4)()
  begin=time.perf_counter_ns()
  assert s.nf_source_packet_bundle_profiled(vb,len(vb),offsets,C.sizeof(offsets),tb,len(tb),tr,C.sizeof(tr),ids,C.sizeof(ids),states,len(states),stats,C.sizeof(stats),self.bundle_timings,C.sizeof(self.bundle_timings))==0
  end=time.perf_counter_ns();w0,w1,c0,c1=self.bundle_timings;self.bundle_transfer_profile=dict(caller_begin_ns=begin,caller_end_ns=end,native_begin_ns=w0,native_end_ns=w1,native_cycles=c1-c0)
  nv,nd,overflow,nt,nb=stats;assert not overflow and nv<=65536 and nd<=4096 and nt<=64 and nb<=16*1024*1024
  vertices=self.vertex_float[:nv];np.copyto(vertices,np.frombuffer(vb,np.float64,count=nv*10).reshape(nv,10),casting="unsafe")
"""+source[end:]
old=' states=self.state_scratch;assert s.nf_source_state_copy(states,nd*72)==0';assert old in source;source=source.replace(old,'')
source=source.replace('(C.c_float*4)(.035,.05,.08,1)','F32_4(.035,.05,.08,1)')
ns=dict(OwnedD3DConsumer.render.__globals__);ns.update(F32_4=F32_4);exec(compile(source,'packet-bundle-render','exec'),ns);OwnedD3DConsumer.render=ns['render']
