import gc,threading,json
from pathlib import Path
from owned_startup_gc_scan_lease_candidate import StartupGCScanLease
original=gc.get_threshold();frozen=gc.get_freeze_count();enabled=gc.isenabled();lease=StartupGCScanLease();lease.enter()
try:
 assert gc.get_threshold()==(original[0],original[1],50)
 errors=[]
 def wrong_owner():
  try:lease.close()
  except RuntimeError:errors.append(True)
 t=threading.Thread(target=wrong_owner);t.start();t.join();assert errors==[True] and lease.active
 try:raise ValueError('simulated failure')
 except ValueError:pass
finally:lease.close()
lease.close();assert gc.get_threshold()==original and gc.get_freeze_count()==frozen and gc.isenabled()==enabled and not lease.sampler.is_alive()
assert not lease.memory_errors and lease.evidence['memory_samples']
Path('work/camera/prototype-runs/gc-lease-lifecycle-20261008.json').write_text(json.dumps(dict(result='PASS_GC_INTERVAL_RESTORATION_MEMORY_OBSERVER',evidence=lease.evidence),indent=2));print('PASS_GC_INTERVAL_RESTORATION_MEMORY_OBSERVER')
