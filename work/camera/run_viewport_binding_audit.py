"""Live original/candidate viewport binding equivalence; diagnostic overhead only."""
import runpy,json,time,atexit,hashlib
from pathlib import Path
import owned_closed_viewport as module
from owned_closed_viewport_cache_candidate import ClosedViewport as Candidate
Original=module.ClosedViewport
checks=[]
class AuditedViewport(Candidate):
 def bind_graph(self,closed):
  before=closed.graph.viewport_data
  candidate=super().bind_graph(closed)
  reference=Original.bind_graph(self,closed)
  assert candidate==reference,'Bound graph fields differ'
  assert candidate.graph.validate()==reference.graph.validate(),'Validated graph differs'
  assert candidate.graph.descriptor_links==reference.graph.descriptor_links,'Descriptor links differ'
  assert closed.graph.viewport_data==before,'Original viewport mutated'
  assert candidate.graph is not closed.graph
  checks.append(dict(epoch=self.epoch,refresh=self.refresh,source=self.source,address=self.address,viewport_hex=self.data.hex(),graph_sha256=hashlib.sha256(candidate.graph.encode()).hexdigest(),validated_nodes=len(candidate.graph.validate())))
  return candidate
module.ClosedViewport=AuditedViewport
def export():
 p=Path('work/camera/prototype-runs')/('viewport-live-binding-'+str(time.time_ns())+'.json')
 p.write_text(json.dumps(dict(result='PASS_CHECKED_BINDINGS' if checks else 'NO_BINDINGS',checks=checks,scope='Same actual original-core viewport and closed graph compared before renderer handoff. Adds reference validation overhead; not timing or final-pixel certification.'),indent=2));print(p)
atexit.register(export)
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')
