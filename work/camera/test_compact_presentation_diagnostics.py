import json
from pathlib import Path
from owned_compact_diagnostics import CompactPresentationDiagnostics
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791376386729745500.json').read_text());ledger=CompactPresentationDiagnostics()
for row in r['presentation_samples']:
 ledger.append(row)
 assert ledger[-1] is row
 assert next(iter(reversed(ledger))) is row
 assert len(ledger)==len(ledger.records)+1
assert ledger.snapshot()==r['presentation_samples']
assert list(reversed(ledger))==list(reversed(r['presentation_samples']))
ledger.flush();assert ledger.tail is None and ledger.snapshot()==r['presentation_samples']
assert ledger.stats()['records']==7162
try:ledger[len(ledger)]
except IndexError:pass
else:raise AssertionError('Out of bounds accepted')
print('PASS 7162 records: mutable latest, reverse pause lookup, full lossless export and final flush')
