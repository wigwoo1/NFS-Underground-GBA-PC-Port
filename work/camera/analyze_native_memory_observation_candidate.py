"""Finite parent-process memory observations, not an indefinite boundedness gate."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['samples'];assert r['exitcode']==0 and len(rows)>=30
assert all(b['seconds']>a['seconds'] for a,b in zip(rows,rows[1:]))
windows=[]
for begin in range(10,60,10):
 bucket=[x for x in rows if begin<=x['seconds']<begin+10]
 if bucket:windows.append(dict(begin_seconds=begin,samples=len(bucket),private_median_mib=statistics.median(x['private_bytes'] for x in bucket)/1048576,private_max_mib=max(x['private_bytes'] for x in bucket)/1048576,working_set_max_mib=max(x['working_set'] for x in bucket)/1048576))
out=dict(result='PASS_MEMORY_OBSERVATION_FORMAT',samples=len(rows),first_seconds=rows[0]['seconds'],last_seconds=rows[-1]['seconds'],windows=windows,private_peak_mib=max(x['private_bytes'] for x in rows)/1048576,scope='Finite parent renderer private/working set observations including startup. Preparation child and GPU excluded; no plateau or indefinite leak-free certification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
