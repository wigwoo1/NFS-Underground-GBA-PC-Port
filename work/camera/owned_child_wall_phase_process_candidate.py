"""Bounded child wall candidate phase probe; original outputs retained."""
import types
import owned_child_road_wrapper_reuse_process_candidate as base
def request_child(*args):
 import time,json,os,inspect,textwrap
 from pathlib import Path
 import owned_motion_wall_regions as walls
 import owned_sampled_graph_wall_visibility as selection
 original=walls.wall_region_candidates;original_selected=selection.wall_region_candidates
 totals={'portal_ns':0,'portal_calls':0,'source_ns':0,'source_calls':0,'candidate_ns':0,'candidate_calls':0}
 def portal(owner,alpha):
  begin=time.perf_counter_ns()
  try:return owner.sample(alpha)
  finally:totals['portal_ns']+=time.perf_counter_ns()-begin;totals['portal_calls']+=1
 def sources(*a,**kw):
  begin=time.perf_counter_ns()
  try:
   # Materialize exactly the generator already fully consumed by candidate code.
   return tuple(walls.wall_sources(*a,**kw))
  finally:totals['source_ns']+=time.perf_counter_ns()-begin;totals['source_calls']+=1
 source=textwrap.dedent(inspect.getsource(original))
 assert source.count('portal_pair.sample(alpha)')==1
 source=source.replace('portal_pair.sample(alpha)','timed_portal(portal_pair,alpha)')
 source=source.replace('for wall in wall_sources(','for wall in timed_sources(')
 ns=dict(original.__globals__,timed_portal=portal,timed_sources=sources)
 exec(compile(source,'wall-phase-probe','exec'),ns);instrumented=ns['wall_region_candidates']
 def candidate(*a,**kw):
  begin=time.perf_counter_ns()
  try:return instrumented(*a,**kw)
  finally:totals['candidate_ns']+=time.perf_counter_ns()-begin;totals['candidate_calls']+=1
 walls.wall_region_candidates=selection.wall_region_candidates=candidate
 try:base.request_child(*args)
 finally:
  walls.wall_region_candidates=original;selection.wall_region_candidates=original_selected
  Path('work/camera/prototype-runs/child-wall-phase-'+str(time.time_ns())+'.json').write_text(json.dumps(dict(pid=os.getpid(),totals=totals,scope='Aggregate actual child portal/wall-source/candidate timing; source generator materialization perturbs allocations. No cadence or output-parity certification.'),indent=2))
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
