import ctypes as C,runpy
from pathlib import Path
mapping={'owned-dx-source-diagnostic-bridge.dll':'owned-dx-source-poll-trace-candidate.dll','owned-frame-handoff.dll':'owned-frame-handoff-precise-candidate.dll','owned-draw-commit-candidate.dll':'owned-draw-commit-precise-candidate.dll','owned-batch-present-candidate.dll':'owned-batch-present-availability-trace-candidate.dll'}
root=Path('work/camera').resolve();original_cdll=C.CDLL;original_pydll=C.PyDLL
loads=[]
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
SourceBatchWorker.__init__=configure
try:runpy.run_path('work/camera/run_playable_input_dxgi_candidate.py',run_name='__main__')
finally:
 import json,time
 Path('work/camera/prototype-runs/precise-loads-'+str(time.time_ns())+'.json').write_text(json.dumps(loads,indent=2));print('precise libraries',loads)


 d=original_cdll(str(root/'owned-dx-source-poll-trace-candidate.dll'));d.nf_dx_display_read.argtypes=[C.c_uint,C.c_void_p];rows=[]
 for i in range(d.nf_dx_display_count()):
  row=(C.c_uint64*14)();assert d.nf_dx_display_read(i,row)==0;rows.append(list(row))
 polls=(C.c_uint64*8)();d.nf_dx_availability_poll_stats.argtypes=[C.c_void_p];assert d.nf_dx_availability_poll_stats(polls)==0
 path=Path('work/camera/prototype-runs/display-ledger-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=rows,dropped=d.nf_dx_display_dropped(),availability_poll_stats=list(polls)),indent=2));print(path)


 b=original_cdll(str(root/'owned-batch-present-availability-trace-candidate.dll'));b.nf_owned_availability_read.argtypes=[C.c_uint,C.c_void_p];timings=[]
 for i in range(b.nf_owned_availability_count()):
  row=(C.c_uint64*14)();assert b.nf_owned_availability_read(i,row)==1;timings.append(list(row))
 path=Path('work/camera/prototype-runs/availability-timings-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=timings,dropped=b.nf_owned_availability_dropped(),fields=['epoch','generation','older','newer','index','deadline_ns','begin_ns','initialize_end_ns','availability_end_ns','draw_end_ns','deadline_wait_end_ns','transaction_end_ns','result_uint64','polls']),indent=2));print(path)
