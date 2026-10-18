"""Bounded exact-content scene road closure cache, owned by one planner."""
import time
from owned_thread_cycles import read as thread_cycles
from owned_closed_scene_memory import scene_memory
from owned_complete_road_candidates import road_candidates
class RoadAssetCache:
 def __init__(self,rom):
  self.rom=rom;self.entries=[];self.bytes=0;self.hits=0;self.misses=0
  self.budget=32*1024*1024;self.capacity=2
 def fork(self):
  other=RoadAssetCache(self.rom);other.entries=list(self.entries);other.bytes=self.bytes
  return other
 def clear(self):self.entries.clear();self.bytes=0
 def get(self,scene):
  self.last_get_stages=[];began=time.perf_counter_ns();cycles=thread_cycles()
  def stage(name):
   nonlocal began,cycles
   end=time.perf_counter_ns();current=thread_cycles()
   self.last_get_stages.append(dict(name=name,started_ns=began,completed_ns=end,wall_ns=end-began,thread_cycles=current-cycles))
   began=end;cycles=current
  for index,(owner,memory,sources,size) in enumerate(self.entries):
   if owner==scene:
    self.entries.append(self.entries.pop(index));self.hits+=1
    stage('cache_hit');return scene,self.rom,memory,sources
  stage('cache_lookup')
  memory=scene_memory(scene,self.rom);stage('scene_memory')
  sources=road_candidates(scene,memory);stage('road_candidates');self.misses+=1
  # Conservative sparse-map accounting plus all uniquely retained byte payloads.
  payloads={id(x):x for row in sources for x in (row.descriptor_bytes,row.vertices,row.offsets,row.face,row.material,row.animation,row.texture) if x is not None}
  g=scene.graph
  size=memory.owned_byte_count+len(memory._ranges)*128+sum(map(len,payloads.values()))+sum(map(len,(g.context,g.geometry,g.offsets,g.materials,scene.objects,scene.callbacks,scene.associations)))
  stage('retained_byte_accounting')
  if size<=self.budget:
   while self.entries and (len(self.entries)>=self.capacity or self.bytes+size>self.budget):self.bytes-=self.entries.pop(0)[3]
   self.entries.append((scene,memory,sources,size));self.bytes+=size
  stage('cache_publication')
  return scene,self.rom,memory,sources
