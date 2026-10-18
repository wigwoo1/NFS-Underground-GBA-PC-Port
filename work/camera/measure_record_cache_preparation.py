"""Count preparation-region record cache hits/misses and logical retained owner bytes."""
import sys,json,runpy
from pathlib import Path
import owned_motion_pairs as module
if '--eight' in sys.argv:
 from owned_record_cache_eight_candidate import install
 install()
reference=module.records;enabled=False;counts=dict(hits=0,misses=0,calls=0,peak_entries=0,peak_logical_owner_bytes=0)
def observe(frame,trace=None):
 if enabled:
  entries=getattr(module._record_cache,'entries',[]);counts['calls']+=1
  counts['hits' if any(x[0] is frame for x in entries) else 'misses']+=1
 value=reference(frame,trace)
 if enabled:
  entries=getattr(module._record_cache,'entries',[]);counts['peak_entries']=max(counts['peak_entries'],len(entries));counts['peak_logical_owner_bytes']=max(counts['peak_logical_owner_bytes'],sum(len(x[0]) for x in entries))
 return value
module.records=observe
source=Path('work/camera/replay_captured_preparation_ready.py').read_text().replace('start=time.perf_counter_ns();cy=cycles();','enabled=True;start=time.perf_counter_ns();cy=cycles();').replace('end=time.perf_counter_ns();ec=cycles()', 'end=time.perf_counter_ns();ec=cycles();enabled=False')
# Function global state and executed replay share this namespace.
exec(compile(source,'record_cache_count_replay','exec'),globals())
Path(sys.argv[1]+'.coverage.json').write_text(json.dumps(dict(counts=counts,scope='Onlyconstruct/precompute; counter overhead; logical frame lengths include shared segmented tails and overestimate physical retained memory. No live timing proof.'),indent=2));print(counts)
