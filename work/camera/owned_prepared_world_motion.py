"""Prepared complete world motion interval with private original-boundary history."""
import time
from owned_thread_cycles import read as thread_cycles
from owned_motion_scene import MotionScene
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_sampled_road_sequence import SampledRoadSequence
from owned_sampled_world_frame import assemble_world
class PreparedWorldMotion:
 def __init__(self,older_frame,newer_frame,older_scene,newer_scene,history,older_roads,rom):
  self.construct_stages=[];stage_start=time.perf_counter_ns();stage_cycles=thread_cycles()
  def stage(name):
   nonlocal stage_start,stage_cycles
   end=time.perf_counter_ns();cycles=thread_cycles()
   self.construct_stages.append(dict(name=name,started_ns=stage_start,completed_ns=end,wall_ns=end-stage_start,thread_cycles=cycles-stage_cycles))
   stage_start=end;stage_cycles=cycles
  older_scene.match(older_frame);stage('older_scene_match')
  newer_scene.match(newer_frame);stage('newer_scene_match')
  if history.epoch!=older_scene.graph.epoch or history.refresh!=older_scene.graph.refresh:raise ValueError('Prepared world history mismatch')
  older_assets=history.assets.get(older_scene.graph);stage('older_road_assets')
  self.construct_stages[-1]['asset_stages']=list(history.assets.last_get_stages)
  newer_assets=history.assets.get(newer_scene.graph);stage('newer_road_assets')
  self.construct_stages[-1]['asset_stages']=list(history.assets.last_get_stages)
  assets=[older_assets,newer_assets]
  self.history=history.fork();self.rom=rom;self.next_history=None
  stage('history_fork')
  try:
   motion=PreparedMotionPair(older_frame,newer_frame,older_scene,newer_scene);portal=PortalMotionPair(older_scene.graph.graph,newer_scene.graph.graph,history.reciprocal,motion,linked_viewports=(older_scene.viewport.horizontal,newer_scene.viewport.horizontal) if older_scene.viewport is not None and newer_scene.viewport is not None else None)
   stage('motion_portal')
   self.pair=CompleteSupplementalCandidates(older_scene.graph,newer_scene.graph,older_scene.supplements,newer_scene.supplements,portal,rom)
   stage('supplement_candidates')
   self.construct_stages[-1]['supplement_stages']=self.pair.construct_stages
   self.roads=SampledRoadSequence(older_scene.graph,newer_scene.graph,portal,self.history,assets=assets)
   stage('road_sequence')
   if hasattr(self.roads,"constructor_stages"):self.construct_stages[-1]["road_constructor_stages"]=self.roads.constructor_stages
   self.next_history=self.history.fork()
   newer_roads,_=self.next_history.plan(newer_scene.graph,assets=assets[1])
   stage('advance_road_history')
   self.construct_stages[-1]['road_advance_stages']=getattr(self.next_history,'plan_stages',[])
   self.construct_stages[-1]['road_advance_stage_dropped']=getattr(self.next_history,'plan_stage_dropped',0)
   self.endpoint_roads=(tuple(older_roads),newer_roads)
  except Exception:self.close();raise
 def take_next_history(self):
  if self.history is None or self.next_history is None:raise ValueError('Advanced road history unavailable')
  result=self.next_history;self.next_history=None;return result
 def sample(self,alpha):
  if self.history is None:raise ValueError('Prepared world interval closed')
  return assemble_world(self.pair,self.roads,self.endpoint_roads,alpha,self.rom)
 def close(self):
  # Release graph-derived caches even if diagnostics retain this closed pair.
  for owner in (getattr(self,'pair',None),getattr(self,'roads',None)):
   portal=getattr(owner,'portal',None)
   if portal is not None:
    for name in ('_wall_material_cache','_wall_source_cache','_wall_metadata_cache'):
     cache=getattr(portal,name,None)
     if cache is not None:cache.clear()
  if self.next_history is not None:self.next_history.close();self.next_history=None
  if self.history is not None:self.history.close();self.history=None

