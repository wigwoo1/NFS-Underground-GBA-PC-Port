"""Isolated combined validation candidates with explicit scanner coverage."""
import runpy,atexit,json,time,threading
from pathlib import Path
import owned_closed_viewport as viewport
from owned_closed_viewport_cache_candidate import ClosedViewport
viewport.ClosedViewport=ClosedViewport
from owned_closed_graph import ClosedGraph
from owned_closed_camera_scan_candidate import ClosedGraph as Scanner
counts={};lock=threading.Lock()
def match(self,frame):
 Scanner.match_frame(self,frame)
 with lock:counts[threading.get_ident()]=counts.get(threading.get_ident(),0)+1
ClosedGraph.match_frame=match
def export():
 p=Path('work/camera/prototype-runs')/('combined-validation-coverage-'+str(time.time_ns())+'.json')
 p.write_text(json.dumps(dict(scanner_calls=sum(counts.values()),owner_threads=counts,scope='Successful candidate scanner calls only. Not pixel/scanout or performance proof.'),indent=2));print(p)
atexit.register(export)
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')
