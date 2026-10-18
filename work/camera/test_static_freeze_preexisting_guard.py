import gc,json
from pathlib import Path
from owned_startup_static_gc_freeze_candidate import StaticFreezeLease
before=dict(frozen=gc.get_freeze_count(),threshold=gc.get_threshold(),enabled=gc.isenabled())
assert before['frozen']>0
lease=StaticFreezeLease()
try:lease.enter()
except ValueError as e:assert str(e)=='Preexisting frozen objects cannot be leased'
else:raise AssertionError('Preexisting freeze accepted')
after=dict(frozen=gc.get_freeze_count(),threshold=gc.get_threshold(),enabled=gc.isenabled())
assert before==after and not lease.active
out=dict(result='PASS_PREEXISTING_FREEZE_GUARD',before=before,after=after,scope='Actual bundled runtime already has permanent-generation objects. Candidate rejected before mutating GC; not installed in live worker.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/vertex-conversion-profile-20261010/static-freeze-guard.json').write_text(json.dumps(out,indent=2));print(out)
