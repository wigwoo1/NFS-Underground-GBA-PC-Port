"""Rank authoritative bridge capture events and reconcile with refresh timing."""
from pathlib import Path
import re,csv,json
p=Path('work/camera')
log=(p/'road-attribute-live-parity.log').read_text()
rows=list(csv.DictReader((p/'original-refresh-profile.csv').open()))
events=[dict(pc=pc,calls=int(calls),ns=int(ns)) for pc,calls,ns in re.findall(r'capture_event_pc=([0-9a-f]+) calls=(\d+) ns=(\d+)',log)]
assert events and len({e['pc'] for e in events})==len(events)
total=sum(e['ns'] for e in events);trace_total=sum(int(r['live_capture_ns']) for r in rows)
# Each accumulated tick count is converted to integer ns independently.
assert abs(total-trace_total)<=len(rows)+len(events)
labels={'03000304':'wall surface audit/extraction and draw palette capture','030032f0':'road surface audit/extraction and draw palette capture','030045e0':'model audit and event dispatch','03004d5c':'visibility builder completion and retained snapshot checks','08002cb4':'visibility query begin and original RAM ownership','030021f8':'region geometry event dispatch'}
for e in events:
 e['label']=labels.get(e['pc'],'capture event; inspect source before attributing a function')
 e['total_ms']=e['ns']/1e6;e['mean_call_ms']=e['ns']/e['calls']/1e6;e['share_percent']=100*e['ns']/total
report=dict(result='PASS',events=len(events),refreshes=len(rows),event_total_ns=total,refresh_capture_total_ns=trace_total,rounding_difference_ns=total-trace_total,ranked_events=sorted(events,key=lambda e:e['ns'],reverse=True),scope='Aggregate event dispatch costs from instrumented original run, reconciled with refresh profile. An event can invoke several handlers; attribution is not exclusive function profiling or whole-route timing proof.')
(p/'capture-event-profile-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
