"""Opt-in overdue display admission; original source samples and clock unchanged."""
import ctypes as C,inspect,time,json,os
from collections import deque
from pathlib import Path
import owned_motion_clock as clock
assert os.environ.get('NFSUG_RETIREMENT_OWNER')=='1'
original=clock.scene_samples;rows=deque(maxlen=8192);stats=dict(caller_intervals=0,examined=0,retired=0,cancelled=0,dropped_records=0)
def selected(origin,base_refresh,older,newer,delay_refreshes=4):
 slots=original(origin,base_refresh,older,newer,delay_refreshes)
 frame=inspect.currentframe().f_back
 try:
  loc=frame.f_locals;worker=loc.get('self')
  active=frame.f_code.co_name=='_draw_intervals' and worker is not None and all(k in loc for k in ('epoch','generation'))
  if not active:return slots
  epoch,generation=loc['epoch'],loc['generation'];pair_begin=loc['pair_begin'];take_begin=loc.get('service_take_begin_ns');take_end=loc.get('service_take_end_ns')
 finally:del frame
 if os.environ.get('NFSUG_CONSUMER_SERVICE_TRACE')=='1':
  import owned_consumer_service_trace_candidate as service_trace
  service_trace.admission_started(pair_begin,older,newer,epoch,generation,take_begin,take_end)
 stats['caller_intervals']+=1
 assert Path(worker.d._name).name=='owned-handoff-request-retirement-candidate.dll'
 assert worker.clock_origin==origin
 def admitted():
  bind=worker.d.nf_owned_handoff_bind_display_clock;bind.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64]
  retire=worker.d.nf_owned_handoff_retire_expired;retire.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_void_p,C.c_size_t]
  for slot in slots:
   if slot['index']<=worker.resume_cutoff:yield slot;continue
   stats['examined']+=1;now=time.perf_counter_ns()
   if now-slot['deadline_ns']<=16666667:yield slot;continue
   rc=bind(worker.owner,epoch,generation,origin)
   if rc==0:stats['cancelled']+=1;return
   assert rc==1
   out=(C.c_uint64*8)();rc=retire(worker.owner,epoch,generation,slot['index'],slot['index'],origin,out,64)
   if rc==0:stats['cancelled']+=1;return
   assert rc==1 and list(out[:4])==[epoch,generation,slot['index'],slot['index']]
   stats['retired']+=1
   if len(rows)==rows.maxlen:stats['dropped_records']+=1
   rows.append(dict(epoch=epoch,generation=generation,index=slot['index'],older=older,newer=newer,origin=origin,deadline_ns=slot['deadline_ns'],alpha=slot['alpha'],native=list(out)))
 return admitted()
clock.scene_samples=selected
def save():
 path=Path('work/camera/prototype-runs')/('expired-admission-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(stats=stats,records=list(rows),scope='Explicit missed display opportunities, not successful frames. Only renderer _draw_intervals filters; source updates/precomputed samples unchanged. Complete if dropped_records=0; no60fps claim.'),indent=2))
 print('EXPIRED_ADMISSION',path,stats,flush=True)
