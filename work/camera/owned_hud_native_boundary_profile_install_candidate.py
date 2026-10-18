"""Isolated native HUD boundary clocks; same functions, buffers and results."""
import owned_segmented_display_placement_install_candidate
import owned_hud_cache_lease_worker_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_renderer_fixed_types_install_candidate
import owned_hud_prefetch_d3d_profile_install_candidate
import owned_packet_profile_install_candidate
import owned_d3d_call_profile_install_candidate
import ctypes as C,inspect,textwrap,threading
from pathlib import Path
import owned_hud_shared_library_binding_candidate as binding
import owned_native_source_hud_cache_lease_session_candidate as session
helper=C.CDLL(str((Path(__file__).parent/'hud-native-boundary-profile-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;S=C.c_size_t
helper.nf_profile_hud_create.argtypes=[P,P,S,U,C.c_uint,C.POINTER(U)];helper.nf_profile_hud_create.restype=U
helper.nf_profile_hud_callback.argtypes=[P,P,S,P,S,U,U,C.POINTER(U)];helper.nf_profile_hud_callback.restype=C.c_int
state=threading.local()
def address(d,name):
 key='_boundary_profile_'+name
 value=d.__dict__.get(key)
 if value is None:value=C.cast(getattr(d,name),P).value;setattr(d,key,value)
 return value

def profile_create(owner,d,ptr,size,epoch,refresh):
 times=(U*3)();result=helper.nf_profile_hud_create(address(d,'nf_hud_owner_create'),ptr,size,epoch,refresh,times);owner.native_create_profile=list(times);return result

def profile_callback(d,ctx,prefix,tail,size,token,epoch):
 times=(U*3)();result=helper.nf_profile_hud_callback(address(d,'nf_owned_gpu_source_segmented_hud_callback'),ctx,prefix,tail,size,token,epoch,times);state.callback=list(times);return result
source=textwrap.dedent(inspect.getsource(binding.HudFrameSnapshot.__init__))
source=source.replace('d.nf_hud_owner_create(ptr,h[3],self.epoch,self.refresh)','profile_create(self,d,ptr,h[3],self.epoch,self.refresh)')
namespace=dict(binding.HudFrameSnapshot.__init__.__globals__,profile_create=profile_create)
exec(compile(source,'hud-snapshot-native-profile','exec'),namespace);binding.HudFrameSnapshot.__init__=namespace['__init__']
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch
source=textwrap.dedent(inspect.getsource(session.NativeSourceSession.prepare))
source=source.replace('snapshot=HudFrameSnapshot(owned.frame.base,native_library=self.source)','snapshot=self._take_hud(owned.frame.base)')
source=source.replace('assert not self.closed', "assert not self.closed\n if self.hud_authority is not None and self.hud_authority!=(epoch,generation):raise NativeFrameIdentityError('Retired HUD prepare generation')")
source=source.replace('source_begin=time.perf_counter_ns();hud_profile=None','source_begin=time.perf_counter_ns();hud_profile=None;self.hud_transfer=None')
source=source.replace('return dict(hud_build_split=', 'return dict(d3d_call_profiles=getattr(self.consumer,"d3d_call_profiles",None),bundle_transfer_profile=getattr(self.consumer,"bundle_transfer_profile",None),hud_transfer=self.hud_transfer,hud_prefetch_taken=self.hud_prefetch_taken,hud_build_split=')
source=source.replace('status=s.nf_owned_gpu_source_segmented_hud_callback(', 'status=profile_callback(s,')
source=source.replace('hud_profile=dict(snapshot_new=', 'hud_profile=dict(native_callback_profile=state.callback,native_create_profile=snapshot.native_create_profile if snapshot_new else None,snapshot_new=')
namespace=dict(prefetch.PrefetchSession.prepare.__globals__,profile_callback=profile_callback,state=state)
exec(compile(source,'hud-session-native-boundaries','exec'),namespace);prefetch.PrefetchSession.prepare=namespace['prepare']
