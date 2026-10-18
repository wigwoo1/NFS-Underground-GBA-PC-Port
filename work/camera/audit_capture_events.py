"""Check event-profile coverage and rank measured live-capture event cost."""
from pathlib import Path
import json,re,sys
p=Path('work/camera');run=json.loads((p/sys.argv[1]).read_text());trace=json.loads((p/sys.argv[2]).read_text())
events=[]
for pc,calls,ns in re.findall(r'capture_event_pc=([0-9a-f]+) calls=(\d+) ns=(\d+)',run['host_output']):
 calls=int(calls);ns=int(ns);assert calls>0
 events.append(dict(pc='0x'+pc,calls=calls,total_ms=ns/1e6,mean_us=ns/calls/1000))
assert events and len({e['pc'] for e in events})==len(events)
profile=trace['profile']['live_capture'];assert sum(e['calls'] for e in events)==profile['calls']
assert abs(sum(e['total_ms'] for e in events)-profile['total_ms'])<.01
report=dict(result='PASS',covered_calls=profile['calls'],events=sorted(events,key=lambda e:e['total_ms'],reverse=True),scope='Exclusive selected live-event detail wall time; aggregate event counters reconcile per-refresh trace. No emulation, other hooks, completed sink or scheduler attribution.')
(p/sys.argv[3]).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
