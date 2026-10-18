"""Reconcile measured audit substages with parent road/wall event costs."""
from pathlib import Path
import re,json
p=Path('work/camera');log=(p/'road-attribute-live-parity.log').read_text()
m=re.search(r'surface_capture_extract_ns=(\d+) surface_capture_defer_ns=(\d+) surface_capture_hash_ns=(\d+) surface_capture_calls=(\d+)',log);assert m
extract,defer,hashing,calls=map(int,m.groups());assert calls
events=[(pc,int(n),int(t)) for pc,n,t in re.findall(r'capture_event_pc=([0-9a-f]+) calls=(\d+) ns=(\d+)',log) if pc in ('03000304','030032f0')]
assert len(events)==2
parent_calls=sum(n for _,n,_ in events);parent_ns=sum(t for _,_,t in events)
assert calls<=parent_calls and extract+defer+hashing<=parent_ns
times=dict(extraction_and_input_validation=extract,differential_deferred_ownership=defer,surface_hashing=hashing,parent_dispatch_other=parent_ns-extract-defer-hashing)
report=dict(result='PASS',audit_calls=calls,parent_event_calls=parent_calls,parent_total_ms=parent_ns/1e6,stages={k:dict(total_ms=v/1e6,mean_audit_call_ms=v/calls/1e6,share_parent_percent=100*v/parent_ns) for k,v in times.items()},scope='Instrumented audit extraction, deferred comparison/ownership/free, and unchanged exact hash. Parent residual includes palette capture/other handlers and timing overhead; no exclusive native game logic or full-route timing proof.')
(p/'surface-capture-profile-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
