"""Opt-in combined callback/stage getter; same native ordering and diagnostics."""
import ctypes as C
from pathlib import Path
import owned_source_packet_phase_profile_install_candidate as profile
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch
P=C.c_void_p;U=C.c_uint64;S=C.c_size_t
helper=C.CDLL(str((Path(__file__).parent/'hud-callback-stage-batch-candidate.dll').resolve()))
helper.nf_profile_hud_callback_stages.argtypes=[P,P,P,S,P,S,U,U,C.POINTER(U),C.POINTER(U),C.POINTER(C.c_int)]
helper.nf_profile_hud_callback_stages.restype=C.c_int
stats=dict(calls=0)
originals=None

def callback(d,ctx,prefix,tail,size,token,epoch):
 times=(U*3)();stages=(U*3)();status=C.c_int()
 begin=profile.source_cycle_read() if profile.cycle_trace else None
 result=helper.nf_profile_hud_callback_stages(profile.address(d,'nf_owned_gpu_source_segmented_hud_callback'),profile.address(d,'nf_owned_gpu_sky_draw_stages'),ctx,prefix,tail,size,token,epoch,times,stages,C.byref(status))
 profile.state.callback=list(times)
 profile.state.callback_outer_cycles=None if not profile.cycle_trace else [begin,profile.source_cycle_read()]
 profile.state.batched_stages=list(stages);profile.state.batched_stage_status=status.value;profile.state.batched_library=d
 stats['calls']+=1
 return result

def read_stages(d):
 if getattr(profile.state,'batched_library',None) is not d:raise RuntimeError('Batch stage owner mismatch')
 if profile.state.batched_stage_status!=0:raise RuntimeError('Source packet stage read rejected')
 return list(profile.state.batched_stages)

def install():
 global originals
 if originals is not None:return
 namespace=prefetch.PrefetchSession.prepare.__globals__
 originals=(namespace,namespace['profile_callback'],namespace['read_packet_stages'])
 namespace['profile_callback']=callback;namespace['read_packet_stages']=read_stages

def uninstall():
 global originals
 if originals is None:return
 namespace,old_callback,old_read=originals;namespace['profile_callback']=old_callback;namespace['read_packet_stages']=old_read;originals=None
