"""Native elapsed versus Windows thread CPU accounting (quantized, not an exclusive scheduler trace)."""
import json,sys,statistics
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text());rows=[]
for r in d['original_update_samples']:
 b=r['native_boundary'];assert len(b)==5 and r['started_ns']<=b[0]<=b[1]<=r['completed_ns'] and b[3]>0 and b[2]!=2**64-1 and b[4]!=2**64-1
 elapsed=b[1]-b[0]
 rows.append(dict(refresh=r['refresh'],native_elapsed_ms=elapsed/1e6,thread_cpu_ms=b[4]/1e6,elapsed_minus_accounted_cpu_ms=(elapsed-b[4])/1e6,native_cycles=b[2],post_return_ms=(r['completed_ns']-b[1])/1e6,capture_profile=r.get('capture_profile')))
result=dict(checked=len(rows),median_elapsed_ms=statistics.median(r['native_elapsed_ms'] for r in rows),median_cpu_ms=statistics.median(r['thread_cpu_ms'] for r in rows),longest=sorted(rows,key=lambda r:r['native_elapsed_ms'],reverse=True)[:16],scope='Windows GetThreadTimes is quantized; elapsed minus accounted CPU is not exact descheduling time. Native call includes capture/emulator/OS work. Raw cycles not converted to time.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
