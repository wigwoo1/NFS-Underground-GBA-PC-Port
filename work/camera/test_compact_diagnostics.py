import json,gc,weakref
from pathlib import Path
from owned_compact_diagnostics import CompactDiagnostics
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791375572279907900.json').read_text())
ledger=CompactDiagnostics()
for row in r['world_preparation_stage_samples']:ledger.append(row)
assert ledger.snapshot()==r['world_preparation_stage_samples']
assert len(ledger)==766 and all(type(x) is bytes and not gc.is_tracked(x) for x in ledger.records)
try:ledger.append(dict(bad=float('nan')))
except ValueError:pass
else:raise AssertionError('Nonfinite accepted')
assert len(ledger)==766
print('PASS 766 complete preparation records lossless; retained bytes untracked; atomic invalid-record rejection')
