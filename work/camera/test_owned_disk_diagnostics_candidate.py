import json,tempfile
from pathlib import Path
from owned_disk_diagnostics_candidate import DiskDiagnostics,DiskPresentationDiagnostics
with tempfile.TemporaryDirectory(dir='work/camera/prototype-runs') as folder:
 for cls in (DiskDiagnostics,DiskPresentationDiagnostics):
  ledger=cls(Path(folder)/(cls.__name__+'.jsonl'));rows=[dict(index=i,payload='x'*(70000+i),nested=[i,None,True]) for i in range(5)]
  for row in rows:ledger.append(row)
  assert ledger.snapshot()==rows
  if cls is DiskPresentationDiagnostics:
   assert list(reversed(ledger))==rows[::-1] and ledger[-1]==rows[-1]
  assert ledger.records[0]==json.dumps(rows[0],separators=(',',':'),allow_nan=False).encode()
  assert len(ledger)==5
  try:ledger.records.append(b'x'*(1024*1024+1))
  except ValueError:pass
  else:raise AssertionError('Oversized spool record accepted')
  ledger.records.close()
print('PASS_DISK_DIAGNOSTIC_RECORDS')

