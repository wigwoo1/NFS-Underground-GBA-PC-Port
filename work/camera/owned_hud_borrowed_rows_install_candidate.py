"""Isolated source setup profiler selection and bounded prepared-frame stamps."""
import ctypes as C,os
from pathlib import Path
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
original_cdll=C.CDLL;loads=[]
def load(path,*args,**kwargs):
 if Path(path).name=='owned-gpu-source-profile-provenance-candidate.dll':
  name='owned-gpu-source-sky-detail-candidate.dll' if os.environ.get('NFSUG_SKY_PACKET_DETAIL')=='1' else 'owned-gpu-hud-borrowed-rows-candidate.dll'
  path=str(Path(path).with_name(name));loads.append(path)
 return original_cdll(path,*args,**kwargs)
C.CDLL=load
original_prepare=PrefetchSession.prepare
def prepare(self,*args,**kwargs):
 result=original_prepare(self,*args,**kwargs);values=(C.c_uint64*4)()
 assert self.source.nf_source_setup_ticks(values)==1
 stamps=list(values);assert stamps==sorted(stamps) and stamps[0]>0
 result['source_setup_ticks']=stamps
 input_values=(C.c_uint64*4)();assert self.source.nf_source_input_ticks(input_values)==1
 inputs=list(input_values);assert inputs==sorted(inputs) and stamps[0]<=inputs[0]<=inputs[-1]<=stamps[1]
 result['source_input_ticks']=inputs
 if hasattr(self.consumer.d,'nf_d3d_hud_discard_stats'):
  discard_stats=(C.c_uint64*8)();fn=self.consumer.d.nf_d3d_hud_discard_stats;fn.argtypes=[C.c_void_p,C.c_size_t];fn.restype=C.c_int;assert fn(discard_stats,C.sizeof(discard_stats))==0;result['hud_discard_stats']=list(discard_stats)
 if hasattr(self.consumer.d,'nf_d3d_hud_phase_cycles'):
  phase_cycles=(C.c_uint64*12)();fn=self.consumer.d.nf_d3d_hud_phase_cycles;fn.argtypes=[C.c_void_p,C.c_size_t];fn.restype=C.c_int;assert fn(phase_cycles,C.sizeof(phase_cycles))==0;result['hud_phase_cycles']=list(phase_cycles)
 self.source.nf_hud_borrowed_input_count.restype=C.c_uint64
 count=self.source.nf_hud_borrowed_input_count();assert count>0
 result['hud_borrowed_input_count']=count
 if os.environ.get('NFSUG_SKY_PACKET_DETAIL')=='1':
  assert Path(self.source._name).name=='owned-gpu-source-sky-detail-candidate.dll'
  detail=(C.c_uint64*16)();fn=self.source.nf_sky_packet_detail;fn.argtypes=[C.c_void_p,C.c_size_t];fn.restype=C.c_int;assert fn(detail,C.sizeof(detail))==0
  result['sky_packet_detail']=list(detail)
  result['sky_packet_detail_library']=Path(self.source._name).name
 if os.environ.get('NFSUG_CLOCK_PRESENT')=='1':
  expected=('owned-d3d-start-floor-present-transaction-candidate.dll' if os.environ.get('NFSUG_PRESENT_FLOOR_START')=='1' else 'owned-d3d-floor-present-transaction-candidate.dll') if os.environ.get('NFSUG_PRESENT_FLOOR')=='1' else 'owned-d3d-clock-present-transaction-candidate.dll'
  assert Path(self.consumer.d._name).name==expected
  q=(C.c_uint64*2)();fn=self.consumer.d.nf_d3d_present_policy;fn.argtypes=[C.c_void_p,C.c_size_t];assert fn(q,C.sizeof(q))==0 and list(q)==[0,0]
  result['present_policy']=list(q);result['present_policy_library']=Path(self.consumer.d._name).name
  if os.environ.get('NFSUG_PRESENT_FLOOR')=='1':
   floor=(C.c_uint64*8)();fn=self.consumer.d.nf_d3d_floor_stats;fn.argtypes=[C.c_void_p,C.c_size_t];assert fn(floor,C.sizeof(floor))==0
   result['present_floor_stats']=list(floor)
 return result
PrefetchSession.prepare=prepare
print('HUD_BORROWED_ROWS_SELECTED',flush=True)


