import json,statistics,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text())['hud_input_profile'];r=p['records'];assert r and p['dropped']==0
assert all(len(x)==7 and x[2] in (0,1) and x[3] in (0,1) and x[6]==(0 if x[3] else 5591040) and (not x[3] or x[2]) for x in r)
o=dict(result='PASS_BOUNDED_INPUT_COMPARE_COPY',records=len(r),dropped=p['dropped'],copied_bytes=sum(x[6] for x in r),groups=[])
for skip in (0,1):
 a=[x for x in r if x[3]==skip]
 if a:o['groups'].append(dict(copy_skipped=bool(skip),count=len(a),median_wall_ms=statistics.median(x[4] for x in a)/1e6,max_wall_ms=max(x[4] for x in a)/1e6,median_cycles=statistics.median(x[5] for x in a)))
o['scope']='Entire incoming exact comparison and conditional owned copy; excludes preceding validation, remaining draw and physical display. No exclusive gain claim.'
Path(sys.argv[2]).write_text(json.dumps(o,indent=2));print(json.dumps(o))
