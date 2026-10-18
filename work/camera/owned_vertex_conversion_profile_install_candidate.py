import ctypes as C
import owned_d3d_call_profile_install_candidate as installed
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_native_callback_cycles_install_candidate import cycles
source=installed.source
old='vertices=self.vertex_float[:nv];np.copyto(vertices,np.frombuffer(vb,np.float64,count=nv*10).reshape(nv,10),casting="unsafe")'
assert source.count(old)==1
new='''conversion_begin=time.perf_counter_ns();conversion_cycles_begin=cycles()
 vertices=self.vertex_float[:nv];np.copyto(vertices,np.frombuffer(vb,np.float64,count=nv*10).reshape(nv,10),casting="unsafe")
 conversion_cycles_end=cycles();conversion_end=time.perf_counter_ns()
 self.vertex_conversion_profile=dict(vertices=nv,draws=nd,begin_ns=conversion_begin,end_ns=conversion_end,thread_cycles=conversion_cycles_end-conversion_cycles_begin)'''
# The source has one-space method indentation after dedent; preserve it.
source=source.replace(old,new.replace('\n ','\n  '))
namespace=dict(OwnedD3DConsumer.render.__globals__);namespace['cycles']=cycles
exec(compile(source,'vertex-conversion-profile','exec'),namespace)
OwnedD3DConsumer.render=namespace['render']
