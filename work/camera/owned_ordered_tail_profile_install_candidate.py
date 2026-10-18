import ctypes as C,types
from pathlib import Path
import owned_ordered_render_tail_install_candidate as ordered
import owned_current_consumer_stage_split_install_candidate as split
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_ordered_render_tail_binding_candidate import Tail,address
bridge=C.CDLL(str(Path(__file__).with_name('ordered-render-tail-profile-candidate.dll').resolve()))
bridge.nf_ordered_render_tail_profile.argtypes=[C.POINTER(Tail),C.c_size_t,C.POINTER(C.c_uint),C.POINTER(C.c_uint64)]
bridge.nf_ordered_render_tail_profile.restype=C.c_int
Ticks=C.c_uint64*7
source=Path(ordered.__file__).read_text().split('source=current.source')[0]
source=source[source.index('def ordered_tail'):]
source=source.replace('result=bridge.nf_ordered_render_tail(C.byref(job),C.sizeof(job),C.byref(failed))','ticks=Ticks();result=bridge.nf_ordered_render_tail_profile(C.byref(job),C.sizeof(job),C.byref(failed),ticks)\n self.ordered_tail_ticks=list(ticks)')
namespace=dict(ordered.ordered_tail.__globals__,bridge=bridge,Ticks=Ticks)
exec(compile(source,'ordered-tail-profile-binding','exec'),namespace)
render_source=split.source.replace("stage('ordered_sky_world_hud')","stage('ordered_sky_world_hud');self.stage_profile[-1]['native_tail_ticks']=self.ordered_tail_ticks")
ns=dict(OwnedD3DConsumer.render.__globals__,ordered_tail=namespace['ordered_tail'])
exec(compile(render_source,'ordered-tail-profile-render','exec'),ns);OwnedD3DConsumer.render=ns['render']
