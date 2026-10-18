import json
from pathlib import Path
from owned_admitted_input_totals_candidate import AdmittedInputTotals
x=AdmittedInputTotals()
for i,k in enumerate([1]*80+[33]*320+[17]*200+[1]*40):x.observe(100+i,k)
assert x.total==640 and x.transitions==3 and x.counts[1]==120 and x.counts[33]==320 and x.counts[17]==200
for r,k in ((800,1024),(800,-1),(739,1)):
 before=x.stats()
 try:x.observe(r,k)
 except ValueError:pass
 else:raise AssertionError('Invalid admission accepted')
 assert x.stats()==before
Path('work/camera/prototype-runs/admitted-input-component-20261008.json').write_text(json.dumps(dict(result='PASS',stats=x.stats(),invalid_data_atomic=True),indent=2));print('PASS admitted key histogram and transition guards')
