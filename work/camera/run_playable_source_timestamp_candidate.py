import ctypes as C,runpy
from pathlib import Path
mapping={'owned-dx-source-diagnostic-bridge.dll':'owned-dx-source-completion-probe-candidate.dll','owned-frame-handoff.dll':'owned-frame-handoff-precise-candidate.dll','owned-draw-commit-candidate.dll':'owned-draw-commit-precise-candidate.dll','owned-batch-present-candidate.dll':'owned-batch-present-source-timestamp-candidate.dll'}
import sys
observation_enabled='--observation-disabled' not in sys.argv
if not observation_enabled:sys.argv.remove('--observation-disabled')
root=Path('work/camera').resolve();original_cdll=C.CDLL;original_pydll=C.PyDLL
loads=[]
config_bridge=original_cdll(str(root/'owned-dx-source-completion-probe-candidate.dll'));config_bridge.nf_dx_observation_configure.argtypes=[C.c_uint];assert config_bridge.nf_dx_observation_configure(int(observation_enabled))==0
def mapped(name):
 p=Path(name)
 if p.parent.resolve()==root and p.name in mapping:
  replacement=str(p.with_name(mapping[p.name]));loads.append([str(p),replacement]);return replacement
 return name
C.CDLL=lambda name,*a,**k:original_cdll(mapped(name),*a,**k)
C.PyDLL=lambda name,*a,**k:original_pydll(mapped(name),*a,**k)
from live_source_batch_candidate import SourceBatchWorker
original_init=SourceBatchWorker.__init__
def configure(self,*args,**kwargs):
 original_init(self,*args,**kwargs)
 self.batch_bridge.nf_owned_display_availability_configure.argtypes=[C.c_void_p,C.c_void_p]
 assert self.batch_bridge.nf_owned_display_availability_configure(C.cast(self.dxgi_bridge.nf_dx_bridge_initialize_callback,C.c_void_p),C.cast(self.dxgi_bridge.nf_dx_availability_poll,C.c_void_p))==1
original_configure=configure
def configure(self,*args,**kwargs):
 original_configure(self,*args,**kwargs)
 self.batch_bridge.nf_owned_prepared_configure.argtypes=[C.c_void_p]*3
 assert self.batch_bridge.nf_owned_prepared_configure(C.cast(self.dxgi_bridge.nf_dx_prepare_callback,C.c_void_p),C.cast(self.dxgi_bridge.nf_dx_abort_prepared,C.c_void_p),C.cast(self.dxgi_bridge.nf_dx_present_prepared_callback,C.c_void_p))==1
previous_configure=configure
def configure(self,*args,**kwargs):
 previous_configure(self,*args,**kwargs)
 self.batch_bridge.nf_owned_source_timestamp_configure.argtypes=[C.c_uint]
 assert self.batch_bridge.nf_owned_source_timestamp_configure(1)==1
SourceBatchWorker.__init__=configure
previous_close=SourceBatchWorker._before_gpu_close
def timestamp_close(self):
 b=self.batch_bridge
 assert b.nf_owned_source_timestamp_shutdown()==0
 stats=(C.c_uint64*3)();b.nf_source_timestamp_stats.argtypes=[C.c_void_p];assert b.nf_source_timestamp_stats(stats)==0
 assert stats[0]==stats[1] and stats[2]==0
 rows=[];b.nf_source_timestamp_read.argtypes=[C.c_uint,C.c_void_p]
 for i in range(b.nf_source_timestamp_count()):
  row=(C.c_uint64*8)();assert b.nf_source_timestamp_read(i,row)==0;rows.append(list(row))
 import json,time
 path=Path('work/camera/prototype-runs/source-gpu-timestamps-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(rows=rows,stats=list(stats),fields=['epoch','generation','index','gpu_begin_ns','gpu_end_ns','cpu_draw_ns','draw_status','query_state'],scope='GPU intervals include scheduling in bracket; unresolved queries canceled on close, no completion wait.'),indent=2));print(path)
 previous_close(self)
SourceBatchWorker._before_gpu_close=timestamp_close
try:runpy.run_path('work/camera/run_playable_input_dxgi_candidate.py',run_name='__main__')
finally:
 import json,time
 Path('work/camera/prototype-runs/precise-loads-'+str(time.time_ns())+'.json').write_text(json.dumps(loads,indent=2));print('precise libraries',loads)


 d=original_cdll(str(root/'owned-dx-source-completion-probe-candidate.dll'));d.nf_dx_display_read.argtypes=[C.c_uint,C.c_void_p];rows=[]
 for i in range(d.nf_dx_display_count()):
  row=(C.c_uint64*14)();assert d.nf_dx_display_read(i,row)==0;rows.append(list(row))
 polls=(C.c_uint64*8)();d.nf_dx_availability_poll_stats.argtypes=[C.c_void_p];assert d.nf_dx_availability_poll_stats(polls)==0
 path=Path('work/camera/prototype-runs/display-ledger-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=rows,dropped=d.nf_dx_display_dropped(),availability_poll_stats=list(polls)),indent=2));print(path)


 b=original_cdll(str(root/'owned-batch-present-source-timestamp-candidate.dll'));b.nf_owned_availability_read.argtypes=[C.c_uint,C.c_void_p];timings=[]
 for i in range(b.nf_owned_availability_count()):
  row=(C.c_uint64*14)();assert b.nf_owned_availability_read(i,row)==1;timings.append(list(row))
 path=Path('work/camera/prototype-runs/availability-timings-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=timings,dropped=b.nf_owned_availability_dropped(),fields=['epoch','generation','older','newer','index','deadline_ns','begin_ns','initialize_end_ns','availability_end_ns','draw_end_ns','deadline_wait_end_ns','transaction_end_ns','result_uint64','polls']),indent=2));print(path)

 d.nf_dx_prepare_read.argtypes=[C.c_uint,C.c_void_p];prepare=[]
 for i in range(d.nf_dx_prepare_count()):
  row=(C.c_uint64*21)();assert d.nf_dx_prepare_read(i,row)==0;prepare.append(list(row))
 path=Path('work/camera/prototype-runs/prepared-transfers-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=prepare,dropped=d.nf_dx_prepare_dropped()),indent=2));print(path)

 d.nf_dx_observation_read.argtypes=[C.c_uint,C.c_void_p];observations=[]
 for i in range(d.nf_dx_observation_count()):
  row=(C.c_uint64*16)();assert d.nf_dx_observation_read(i,row)==0;observations.append(list(row))
 path=Path('work/camera/prototype-runs/display-observations-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=observations,dropped=d.nf_dx_observation_dropped(),points=['after_prepare','before_present','after_present','explicit_tail']),indent=2));print(path)

 d.nf_dx_completion_read.argtypes=[C.c_uint,C.c_void_p];completion=[]
 for i in range(d.nf_dx_completion_count()):
  row=(C.c_uint64*15)();assert d.nf_dx_completion_read(i,row)==0;completion.append(list(row))
 path=Path('work/camera/prototype-runs/gpu-completion-probes-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=completion,dropped=d.nf_dx_completion_dropped(),fields=['epoch','generation','index','world_before_lock','world_after_lock','blit_before_unlock','blit_after_unlock','created','deleted','world_before_poll_ns','world_after_poll_ns','blit_before_poll_ns','blit_after_poll_ns','gl_error','status']),indent=2));print(path)
