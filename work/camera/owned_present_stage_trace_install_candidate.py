"""Isolated present-stage timing without changing native calls/order."""
import ctypes as C,time
from owned_uncovered_window_candidate import OwnedD3DConsumer

def present(self):
 begin=time.perf_counter_ns();state=(C.c_uint64*7)();assert self.d.nf_d3d_window_pump(self.window,state)==0;pumped=time.perf_counter_ns()
 status=self.d.nf_d3d_present();presented=time.perf_counter_ns();assert status in (0,3)
 stats=(C.c_uint64*9)();self.d.nf_d3d_display_stats.argtypes=[C.c_void_p];assert self.d.nf_d3d_display_stats(stats)==0;queried=time.perf_counter_ns()
 return dict(status=status,window=list(state),dxgi_display_stats=list(stats),present_stage_ns=dict(begin=begin,pumped=pumped,presented=presented,queried=queried))
OwnedD3DConsumer.present=present
