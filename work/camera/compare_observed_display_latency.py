import json,statistics,sys
from pathlib import Path
results=[]
for name in sys.argv[1:3]:
 rows=json.loads(Path(name).read_text())['rows'];sub={};seen=set();delays=[]
 for t in rows:
  assert t[5]==0 and t[6]==t[4];sub[t[6]]=t[2]*1000000000//t[3]
  if t[7]!=0 or not t[8] or t[9]!=t[10] or t[8] in seen:continue
  assert t[8] in sub;seen.add(t[8]);delays.append((t[11]*1000000000//t[3]-sub[t[8]])/1e6)
 assert delays and min(delays)>=0
 values=sorted(delays);results.append(dict(ledger=name,observed=len(values),median_callback_end_to_display_ms=statistics.median(values),p95_ms=values[int(.95*(len(values)-1))],max_ms=max(values)))
out=dict(result='OBSERVED_DISPLAY_LATENCY_COMPARISON',runs=results,scope='First observed flip ID, exact successful callback end; timestamps accepted only when SyncRefresh equals PresentRefresh. Sequential uncontrolled runs; not input latency or physical4K proof.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out)
