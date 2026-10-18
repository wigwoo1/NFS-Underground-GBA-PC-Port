"""Isolated synchronous draw tail; existing source and backend checks retained."""
import ctypes as C
import owned_d3d_call_profile_install_candidate as current
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_ordered_render_tail_binding_candidate import Tail,bridge,address

def ordered_tail(self,s,vertices,nv,offsets,ids,states,nd):
 d=self.d
 job=Tail(address(d.nf_d3d_source_sky_pan_batch),address(d.nf_d3d_world_batch),address(d.nf_d3d_source_hud_batch),address(s.nf_source_sky_info),address(s.nf_source_sky_copy),address(s.nf_source_hud_planes_info),address(s.nf_source_hud_plane_copy),address(s.nf_source_hud_batches_count),address(s.nf_source_hud_batches_copy),vertices.ctypes.data,nv,vertices.nbytes,C.addressof(offsets),(nd+1)*4,C.addressof(ids),nd*4,C.addressof(states),nd,nd*72)
 failed=C.c_uint()
 result=bridge.nf_ordered_render_tail(C.byref(job),C.sizeof(job),C.byref(failed))
 if result:raise RuntimeError(f'Ordered native draw failed: status={result}, stage={failed.value}')
 self.ordered_tail_completed=True

source=current.source
start=source.index('  assert d.nf_d3d_source_sky_pan_batch(')
end=source.index("  stage('background_copy_hud_upload_draw')",start)+len("  stage('background_copy_hud_upload_draw')")
source=source[:start]+"  ordered_tail(self,s,vertices,nv,offsets,ids,states,nd)\n  stage('ordered_sky_world_hud')"+source[end:]
ns=dict(OwnedD3DConsumer.render.__globals__);ns.update(ordered_tail=ordered_tail)
exec(compile(source,'ordered-native-render-tail','exec'),ns)
OwnedD3DConsumer.render=ns['render']

