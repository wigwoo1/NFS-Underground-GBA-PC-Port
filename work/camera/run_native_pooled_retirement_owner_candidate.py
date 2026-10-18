"""Opt-in unified pooled owner/commit routing; retirement remains disabled."""
import ctypes as C,runpy,json,os
from pathlib import Path
assert os.environ.get('NFSUG_RETIREMENT_OWNER')=='1'
assert os.environ.get('NFSUG_PRESENT_FLOOR')!='1' and os.environ.get('NFSUG_CLOCK_PRESENT')!='1'
original=C.CDLL;loads=[]
def selected(path,*args,**kwargs):
 name=Path(str(path)).name
 if name in ('owned-handoff-request-authority-candidate.dll','owned-draw-commit-integer-clock-candidate.dll'):
  path=str(Path(path).with_name('owned-handoff-request-retirement-candidate.dll'))
 d=original(path,*args,**kwargs)
 if name in ('owned-handoff-request-authority-candidate.dll','owned-draw-commit-integer-clock-candidate.dll'):
  assert Path(d._name).name=='owned-handoff-request-retirement-candidate.dll'
  assert all(hasattr(d,export) for export in ('nf_owned_handoff_create_capacity','nf_owned_handoff_push_authority','nf_owned_handoff_pool_stats','nf_owned_handoff_draw_wait_commit_sample','nf_owned_handoff_retire_expired','nf_owned_handoff_bind_display_clock'))
  loads.append(dict(requested=name,loaded=d._name))
 return d
C.CDLL=selected
if os.environ.get('NFSUG_EXPIRED_ADMISSION')=='1':import owned_expired_slot_admission_candidate as admission
if os.environ.get('NFSUG_CONSUMER_SERVICE_TRACE')=='1':
 assert os.environ.get('NFSUG_EXPIRED_ADMISSION')=='1'
 import owned_consumer_service_trace_candidate as service_trace
try:
 runpy.run_path('work/camera/run_native_sky_reader_bulk.py',run_name='__main__')
 assert set(x['requested'] for x in loads)=={'owned-handoff-request-authority-candidate.dll','owned-draw-commit-integer-clock-candidate.dll'}
 result='PASS_LIVE_UNIFIED_POOLED_OWNER_COMMIT_SELECTION'
finally:
 if os.environ.get('NFSUG_CONSUMER_SERVICE_TRACE')=='1':service_trace.save()
 if os.environ.get('NFSUG_EXPIRED_ADMISSION')=='1':admission.save()
 C.CDLL=original
 out=dict(result=locals().get('result','FAILED_LIVE_ROUTING'),loads=loads,retirement_enabled=os.environ.get('NFSUG_EXPIRED_ADMISSION')=='1',scope='Current live renderer selected pooled isolated DLL for owner and commit routes; Retirement selection reported separately; consult explicit missed-slot ledger. No timing/throughput/pixel/scanout qualification.')
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/pooled-retirement-component-20261010/live-recovery-routing.json').write_text(json.dumps(out,indent=2));print('RETIREMENT_OWNER_ROUTING',out['result'],flush=True)


