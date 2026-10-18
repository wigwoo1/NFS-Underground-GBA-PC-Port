"""Isolated bounded scalar availability margins; no timing or sample policy changes."""
import inspect,textwrap,time,json
from pathlib import Path
from owned_progressive_pair_candidate import ProgressivePair
from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
rows=[];dropped=0
source=inspect.getsource(ProgressivePair.publish)
needle='   if not self.first.done():';assert source.count(needle)==1
source=source.replace(needle,"   if not hasattr(self,'_margin_ready'):self._margin_ready={}\n   self._margin_ready[a]=time.perf_counter_ns()\n"+needle)
ns=dict(ProgressivePair.publish.__globals__);exec(compile(textwrap.dedent(source),'sample-margin-publication','exec'),ns);ProgressivePair.publish=ns['publish']
def record(pair,alpha,begin,end,kind):
 global dropped
 ready=pair._margin_ready[alpha]
 assert ready<=end
 row=dict(kind=kind,identity=pair._margin_identity,alpha=alpha,ready_ns=ready,requested_ns=begin,returned_ns=end,available_before_request_ns=begin-ready)
 if len(rows)<8192:rows.append(row)
 else:dropped+=1
sample=ProgressivePair.sample
def observed_sample(self,alpha,timeout=20):
 begin=time.perf_counter_ns();result=sample(self,alpha,timeout);end=time.perf_counter_ns();record(self,alpha,begin,end,'sample');return result
ProgressivePair.sample=observed_sample
# Use the existing transformed submit source, retaining queue timestamps.
import owned_preparation_queue_lead_install_candidate as queue_setup
# Reconstruct from the original adapter file AST rather than transformed inspect metadata.
import ast
module=ast.parse(Path('work/camera/owned_progressive_preparation_adapter_candidate.py').read_text());cls=next(x for x in module.body if isinstance(x,ast.ClassDef) and x.name=='ProgressivePreparationAdapter');node=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='submit');source=ast.unparse(node)
needle='self.jobs.put((self.generation, older, newer, pair))';assert source.count(needle)==1
source=source.replace(needle,"pair._margin_identity=(self.generation,older[1].graph.refresh,newer[1].graph.refresh)\n        pair._queue_submitted_ns=time.perf_counter_ns()\n        "+needle)
ns=dict(Adapter.submit.__globals__);exec(compile(source,'sample-margin-submit','exec'),ns);Adapter.submit=ns['submit']
take=Adapter.take
def observed_take(self,future,timeout=30):
 begin=time.perf_counter_ns();pair=take(self,future,timeout);end=time.perf_counter_ns()
 if pair.alphas:record(pair,pair.alphas[0],begin,end,'first_take')
 return pair
Adapter.take=observed_take
def save():
 path=Path('work/camera/prototype-runs/sample-readiness-margin-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=rows,dropped=dropped,scope='Publication availability versus actual API request, not ideal presentation deadline. First future wait separately recorded; bounded scalar rows only.'),indent=2));print('SAMPLE_READINESS_MARGIN',path,flush=True)
