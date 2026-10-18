"""Sequential original-boundary CPU history behind bounded preparation futures."""
import struct,time,threading
from pathlib import Path
from owned_preparation_pipeline import PreparationPipeline
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
class WorldPreparationService:
 def __init__(self,rom,capacity):
  self.profile_refresh=None;self.profiles=[];self.cache_diagnostic_range=None;self.cache_diagnostics=[]
  self.rom=rom;self.pipeline=PreparationPipeline(capacity);self.history=None;self.roads=None;self.generation=None
  self.table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
 def warm_start(self,frame,scene):
  """Prepare only the already captured first boundary, before live clock."""
  scene.match(frame);generation=self.pipeline.generation
  class Ready:
   def __init__(self,evidence):self.evidence=evidence
   def close(self):pass
  def initialize():
   if self.history is not None:raise ValueError('Startup history already initialized')
   began=time.perf_counter_ns()
   self.history=EndpointRoadPlanner(self.rom,self.table)
   self.roads,_=self.history.plan(scene.graph);self.generation=generation
   from sample_owned_motion import rigid_library
   rigid_library()
   return Ready(dict(epoch=self.history.epoch,refresh=self.history.refresh,worker=threading.get_ident(),wall_ns=time.perf_counter_ns()-began))
  future=self.pipeline.submit(initialize,timeout=30)
  return self.pipeline.take(future).evidence
 def submit(self,older,newer,alphas=None,timeout=0,abort=None):
  generation=self.pipeline.generation
  def prepare():
   started=time.perf_counter_ns();cpu_started=time.thread_time_ns();a,sa=older;b,sb=newer
   cache_before=None
   if self.cache_diagnostic_range is not None and self.cache_diagnostic_range[0]<=sa.graph.refresh<=self.cache_diagnostic_range[1]:
    from owned_cache_diagnostics import snapshot
    cache_before=snapshot()
   if self.history is None or self.generation!=generation or self.history.epoch!=sa.graph.epoch or self.history.refresh!=sa.graph.refresh:
    if self.history is not None:self.history.close()
    self.history=EndpointRoadPlanner(self.rom,self.table);self.roads,_=self.history.plan(sa.graph);self.generation=generation
   if self.profile_refresh==sa.graph.refresh and getattr(self,'profile_capture_folder',None) is not None:
    import json
    from owned_road_history_diagnostic import snapshot
    (self.profile_capture_folder/'road-history.json').write_text(json.dumps(dict(epoch=self.history.epoch,refresh=self.history.refresh,scratch=snapshot(self.history.scratch)),indent=2))
    from owned_road_record_diagnostic import encode,decode
    encoded_roads=encode(self.roads)
    if decode(json.loads(json.dumps(encoded_roads)))!=self.roads:raise ValueError('Road diagnostic roundtrip mismatch')
    (self.profile_capture_folder/'older-roads.json').write_text(json.dumps(encoded_roads))
   result=PreparedWorldMotion(a,b,sa,sb,self.history,self.roads,self.rom)
   try:
    advanced=result.take_next_history()
    self.history.close();self.history=advanced;self.roads=result.endpoint_roads[1]
   except BaseException:result.close();raise
   constructed=time.perf_counter_ns();cpu_constructed=time.thread_time_ns()
   if alphas is not None:
    from owned_precomputed_world_samples import PrecomputedWorldSamples
    result=PrecomputedWorldSamples(result,alphas,trace=True)
   if self.profile_refresh==sa.graph.refresh and getattr(self,'profile_capture_folder',None) is not None and alphas is not None:
    import json
    from owned_sample_signature import signature
    (self.profile_capture_folder/'prepared-signatures.json').write_text(json.dumps([dict(alpha=alpha,signature=signature(result.sample(alpha))) for alpha in alphas],indent=2))
   completed=time.perf_counter_ns();cpu_completed=time.thread_time_ns()
   if cache_before is not None:
    self.cache_diagnostics.append(dict(older=sa.graph.refresh,newer=sb.graph.refresh,alpha_count=len(alphas) if alphas is not None else None,before=cache_before,after=snapshot()))
    if len(self.cache_diagnostics)>128:self.cache_diagnostics.pop(0)
   if not hasattr(self,'stage_samples'):self.stage_samples=[]
   if len(self.stage_samples)<10000:self.stage_samples.append(dict(thread_id=threading.get_ident(),older=sa.graph.refresh,newer=sb.graph.refresh,construct_advance_ns=constructed-started,precompute_ns=completed-constructed,started_ns=started,constructed_ns=constructed,completed_ns=completed,construct_thread_cpu_ns=cpu_constructed-cpu_started,precompute_thread_cpu_ns=cpu_completed-cpu_constructed,sample_timings=getattr(result,'sample_timings',[]),prepared_close_ns=getattr(result,'prepared_close_ns',None)))
   return result
  def measured_prepare():
   if self.profile_refresh is None or older[1].graph.refresh!=self.profile_refresh or self.profiles:return prepare()
   # Explicit diagnostics only; capture immutable inputs before profiling.
   folder=Path('work/camera/prototype-runs')/('profile-scene-'+str(time.time_ns()));folder.mkdir()
   for label,(frame,owned) in zip(('older','newer'),(older,newer)):
    (folder/(label+'.frame.bin')).write_bytes(frame)
    (folder/(label+'.graph.bin')).write_bytes(owned.graph.graph.encode())
    for section in ('objects','callbacks','associations'):(folder/(label+'.'+section+'.bin')).write_bytes(getattr(owned.graph,section))
    if owned.builders is not None:(folder/(label+'.builders.bin')).write_bytes(owned.builders.payload)
    if owned.sources is not None:(folder/(label+'.current-sources.bin')).write_bytes(owned.sources.payload)
    supplements=owned.supplements
    packet=struct.pack('<6IQ',0x3143534e,1,supplements.refresh,supplements.source_refresh,len(supplements.geometry),len(supplements.textures),supplements.epoch)+supplements.geometry+supplements.textures
    (folder/(label+'.supplements.bin')).write_bytes(packet)
   import json
   (folder/'capture.json').write_text(json.dumps(dict(older=older[1].identity,newer=newer[1].identity,alphas=alphas,scope='Immutable scene inputs with live planner scratch, older roads and prepared signatures captured during this diagnostic job'),indent=2))
   self.profile_capture_folder=folder
   from owned_thread_profile import ThreadProfile
   profile=ThreadProfile();output=Path('work/camera/prototype-runs')/('live-preparation-'+str(time.time_ns())+'.thread-profile.json')
   self.profiles.append(dict(thread_id=threading.get_ident(),older=older[1].graph.refresh,newer=newer[1].graph.refresh,profile=str(output),capture=str(folder),scope='explicit owner-thread Python inclusive wall times; profiler overhead and scheduling waits included'))
   try:return profile.run(prepare)
   finally:profile.save(output)
  return self.pipeline.submit(measured_prepare,timeout=timeout,abort=abort)
 def invalidate(self):self.pipeline.invalidate()
 def take(self,future):return self.pipeline.take(future)
 def close(self):
  self.pipeline.close()
  if self.history is not None:self.history.close();self.history=None
