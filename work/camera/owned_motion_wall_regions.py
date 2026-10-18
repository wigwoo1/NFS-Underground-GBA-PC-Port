"""Complete owned wall candidates and continuous portal clips for sampled motion."""
from dataclasses import dataclass
import math,os,time
from owned_thread_cycles import read as thread_cycles
from owned_graph_wall_sources import wall_sources,WallSource
from owned_wall_region_candidates import hidden
@dataclass(frozen=True)
class WallRegionCandidate:
 ordinal:int
 descriptor:int
 edge:int
 bounds:tuple
 region_flags:int
 wall:WallSource

def _plain_wall_region_candidates(portal_pair,alpha,*,queue=None):
 # Material animation and offsets stay at the older endpoint until alpha1.
 # Surface near clipping/frontface/deferred ordering are a later stage.
 queue=portal_pair.sample(alpha) if queue is None else tuple(queue)
 graph=portal_pair.newer if alpha==1 else portal_pair.older
 if not hasattr(portal_pair,'_wall_source_cache'):portal_pair._wall_source_cache=[]
 cached=next((sources for owner,sources in portal_pair._wall_source_cache if owner is graph),None)
 if cached is None:
  graph.validate();cached={}
  portal_pair._wall_source_cache.append((graph,cached))
  if len(portal_pair._wall_source_cache)>2:portal_pair._wall_source_cache.pop(0)
 needed={region[0] for region in queue if not region[5]&8 and region[1]<=region[2] and region[3]<=region[4]}-cached.keys()
 if needed:
  if not hasattr(portal_pair,'_wall_material_cache'):portal_pair._wall_material_cache=[]
  material_cache=next((entry for entry in portal_pair._wall_material_cache if entry[0] is graph),None)
  if material_cache is None:
   material_cache=[graph,None];portal_pair._wall_material_cache.append(material_cache)
   if len(portal_pair._wall_material_cache)>2:portal_pair._wall_material_cache.pop(0)
  groups={key:[] for key in needed}
  for wall in wall_sources(graph,validated=True,descriptors=needed,material_cache=material_cache):
   if not hidden(wall):groups[wall.descriptor].append(wall)
  cached.update({key:tuple(value) for key,value in groups.items()})
 sources=cached
 out=[]
 for ordinal,region in enumerate(queue):
  if region[5]&8:continue
  bounds=tuple(float(x) for x in region[1:5])
  if not all(math.isfinite(x) for x in bounds):raise ValueError('Nonfinite sampled wall clip')
  # Empty portal intersections supply no drawable candidate; do not clamp them.
  if bounds[0]>bounds[1] or bounds[2]>bounds[3]:continue
  for wall in sources.get(region[0],()):out.append(WallRegionCandidate(ordinal,region[0],wall.edge,bounds,region[5],wall))
 return tuple(out)


def _traced_wall_region_candidates(portal_pair,alpha,*,queue=None):
 # Material animation and offsets stay at the older endpoint until alpha1.
 # Surface near clipping/frontface/deferred ordering are a later stage.
 tracing=os.environ.get('NFSUG_WALL_CANDIDATE_TRACE')=='1'
 portal_pair._last_wall_candidate_stages=[] if tracing else None
 if tracing:start=time.perf_counter_ns();cycles=thread_cycles()
 def stage(name):
  nonlocal start,cycles
  if not tracing:return
  end=time.perf_counter_ns();at=thread_cycles();portal_pair._last_wall_candidate_stages.append(dict(name=name,started_ns=start,completed_ns=end,wall_ns=end-start,thread_cycles=at-cycles));start=end;cycles=at
 queue=portal_pair.sample(alpha) if queue is None else tuple(queue)
 graph=portal_pair.newer if alpha==1 else portal_pair.older
 stage('queue_and_graph')
 if not hasattr(portal_pair,'_wall_source_cache'):portal_pair._wall_source_cache=[]
 cached=next((sources for owner,sources in portal_pair._wall_source_cache if owner is graph),None)
 if cached is None:
  graph.validate();cached={}
  portal_pair._wall_source_cache.append((graph,cached))
  if len(portal_pair._wall_source_cache)>2:portal_pair._wall_source_cache.pop(0)
 stage('cache_lookup_and_validation')
 needed={region[0] for region in queue if not region[5]&8 and region[1]<=region[2] and region[3]<=region[4]}-cached.keys()
 stage('needed_descriptors')
 if needed:
  if not hasattr(portal_pair,'_wall_material_cache'):portal_pair._wall_material_cache=[]
  material_cache=next((entry for entry in portal_pair._wall_material_cache if entry[0] is graph),None)
  if material_cache is None:
   material_cache=[graph,None];portal_pair._wall_material_cache.append(material_cache)
   if len(portal_pair._wall_material_cache)>2:portal_pair._wall_material_cache.pop(0)
  groups={key:[] for key in needed}
  for wall in wall_sources(graph,validated=True,descriptors=needed,material_cache=material_cache):
   if not hidden(wall):groups[wall.descriptor].append(wall)
  cached.update({key:tuple(value) for key,value in groups.items()})
 stage('material_and_wall_source_decode')
 sources=cached
 out=[]
 for ordinal,region in enumerate(queue):
  if region[5]&8:continue
  bounds=tuple(float(x) for x in region[1:5])
  if not all(math.isfinite(x) for x in bounds):raise ValueError('Nonfinite sampled wall clip')
  # Empty portal intersections supply no drawable candidate; do not clamp them.
  if bounds[0]>bounds[1] or bounds[2]>bounds[3]:continue
  for wall in sources.get(region[0],()):out.append(WallRegionCandidate(ordinal,region[0],wall.edge,bounds,region[5],wall))
 result=tuple(out);stage('candidate_assembly');return result


# Select once per process; ordinary sampling has no profiling bookkeeping.
wall_region_candidates=_traced_wall_region_candidates if os.environ.get('NFSUG_WALL_CANDIDATE_TRACE')=='1' else _plain_wall_region_candidates
