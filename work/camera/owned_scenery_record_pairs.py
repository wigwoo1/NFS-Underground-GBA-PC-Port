"""Complete immutable candidate records paired by original source identity."""
from dataclasses import dataclass
import os
from owned_ordinary_model_visits import ordinary_model_visits
from owned_model_record_builder import ModelRecordBuilder
from owned_object_filter import depth_distance
from owned_removed_scenery_visit import removed_scenery_visit,depth_hidden_scenery_visit,portal_hidden_scenery_visit
import threading

_record_builder_local=threading.local()
_fine_parity_trace=os.environ.get("NFSUG_SCENERY_PAIR_FINE_TRACE")=="1"

def _record_builder_for_rom(rom):
 # A prepared interval owns only byte records, while the builder's private scene
 # memory is already bounded to its last two graph snapshots. Reuse it on the
 # same immutable ROM object so constructor/DLL setup does not land on a later
 # transition. Thread-local ownership avoids cross-worker mutation.
 if isinstance(rom,bytes):
  cached=getattr(_record_builder_local,"entry",None)
  if cached is not None and cached[0] is rom:return cached[1],True
 builder=ModelRecordBuilder(rom)
 if isinstance(rom,bytes):_record_builder_local.entry=(rom,builder)
 return builder,False

@dataclass(frozen=True)
class SceneryRecordPair:
 object_index:int
 older_blocks:tuple
 newer_blocks:tuple
 older_allocated:bool
 newer_allocated:bool

def prepare_scenery_record_pairs(scenes,queues,rom,object_indices=None,timing=None):
 if timing is not None:
  import time
  from owned_thread_cycles import read as thread_cycles
  phase_started=time.perf_counter_ns();phase_cycles=thread_cycles()
  def phase(name,**detail):
   nonlocal phase_started,phase_cycles
   now=time.perf_counter_ns();cycles=thread_cycles()
   timing.append(dict(phase=name,wall_ns=now-phase_started,thread_cycles=cycles-phase_cycles,**detail))
   phase_started=now;phase_cycles=cycles
 else:phase=None
 scenes=tuple(scenes);queues=tuple(queues)
 if len(scenes)!=2 or len(queues)!=2:raise ValueError('Incomplete scenery record pair')
 builder,builder_cache_hit=_record_builder_for_rom(rom);maps=[]
 if phase:phase("builder_init",cache_hit=builder_cache_hit)
 for scene,queue in zip(scenes,queues):
  visits={}
  visit_count=0
  for visit in ordinary_model_visits(scene.graph,queue,True):
   visit_count+=1
   if object_indices is not None and visit['object'] not in object_indices:continue
   if not 30<=visit['dispatch']['model']<=36:continue
   if visit['object'] in visits:raise ValueError('Repeated scenery candidate')
   visits[visit['object']]=visit
  maps.append(visits)
  if phase:phase("endpoint_candidate_visits",refresh=scene.graph.refresh,visit_count=visit_count,candidate_count=len(visits))
 if len(maps)!=2:raise ValueError('Incomplete scenery record pair')
 removed=set();depth_hidden=set();portal_hidden=set()
 if object_indices is not None:
  for index in set(object_indices)&maps[0].keys()-maps[1].keys():
   import struct
   source=scenes[1].sources.sources.get(struct.unpack_from('<I',scenes[1].graph.graph.context,60)[0]+index*164) if scenes[1].sources else None
   if source is not None and source[136]!=255 and depth_distance(source,scenes[1].graph.graph.context[256:304])[0]>0:
    maps[1][index]=portal_hidden_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);portal_hidden.add(index)
   elif source is not None and source[136]!=255:
    maps[1][index]=depth_hidden_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);depth_hidden.add(index)
   else:
    maps[1][index]=removed_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);removed.add(index)
 if phase:phase("missing_visit_resolution",removed=len(removed),depth_hidden=len(depth_hidden),portal_hidden=len(portal_hidden))

 if object_indices is not None and any(set(m)!=set(object_indices) for m in maps):raise ValueError('Missing transition scenery candidate')
 if maps[0].keys()!=maps[1].keys():raise ValueError('Scenery candidate source population changed')
 if phase:phase("candidate_set_validation",older=len(maps[0]),newer=len(maps[1]))
 out=[]
 for index,a in maps[0].items():
  b=maps[1][index]
  if any(a['dispatch'].get(k)!=b['dispatch'].get(k) for k in ('model','variant','descriptor')):raise ValueError('Scenery candidate identity changed')
  if timing is not None:
   import time
   from owned_thread_cycles import read as thread_cycles
   build_started=time.perf_counter_ns();build_cycles=thread_cycles()
  blocks=(builder.prepare_visit(scenes[0],queues[0],a),builder.prepare_removed(*scenes,*queues,index)) if index in removed else (None,None) if index in depth_hidden or index in portal_hidden else tuple(builder.prepare_far_hidden(scene,queue,visit) if visit['depth']>=8192 else builder.prepare_visit(scene,queue,visit) for scene,queue,visit in zip(scenes,queues,(a,b)))
  if index in portal_hidden:blocks=(builder.prepare_visit(scenes[0],queues[0],a),builder.prepare_portal_hidden(*scenes,*queues,index))
  if index in depth_hidden:blocks=(builder.prepare_visit(scenes[0],queues[0],a),builder.prepare_depth_hidden(*scenes,*queues,index))
  if timing is not None:timing.append(dict(owner=index,model=a['dispatch']['model'],variant=a['dispatch'].get('variant'),wall_ns=time.perf_counter_ns()-build_started,thread_cycles=thread_cycles()-build_cycles))
  if _fine_parity_trace and timing is not None:
   from owned_thread_cycles import read as thread_cycles
   parity_started=time.perf_counter_ns();parity_cycles=thread_cycles();checks=[]
   for block_index in (1,4,5,6,7,8,10):
    check_started=time.perf_counter_ns();check_cycles=thread_cycles()
    equal=blocks[0][block_index]==blocks[1][block_index]
    checks.append(dict(block=block_index,equal=equal,older_bytes=len(blocks[0][block_index]),newer_bytes=len(blocks[1][block_index]),wall_ns=time.perf_counter_ns()-check_started,thread_cycles=thread_cycles()-check_cycles))
    if not equal:raise ValueError('Scenery topology/material transition')
   timing.append(dict(phase="exact_topology_material_parity",owner=index,wall_ns=time.perf_counter_ns()-parity_started,thread_cycles=thread_cycles()-parity_cycles,checks=checks))
  elif any(blocks[0][i]!=blocks[1][i] for i in (1,4,5,6,7,8,10)):raise ValueError('Scenery topology/material transition')
  out.append(SceneryRecordPair(index,*blocks,a['allocated'],b['allocated']))
 if phase:phase("pair_publication",record_count=len(out))
 return tuple(out)


def captured_scenery_record_pairs(scenes,queues,frames,owner_maps,rom,indices,decoded_rows=None):
 """Use complete original draws only after exact source/builder ownership proof."""
 import struct
 from owned_motion_pairs import records
 from owned_scenery_projection import SceneryProjection
 projection=SceneryProjection(rom);visits=[{v['object']:v for v in ordinary_model_visits(scene.graph,queue)} for scene,queue in zip(scenes,queues)];rows=[records(frame)['records'] for frame in frames] if decoded_rows is None else decoded_rows;out=[]
 for owner in sorted(indices):
  blocks=[];dispatch=[]
  for endpoint,scene in enumerate(scenes):
   visit=visits[endpoint].get(owner)
   if visit is None or not visit['allocated'] or not 30<=visit['dispatch']['model']<=36:raise ValueError('Unverified captured scenery source')
   index=next(i for i,value in owner_maps[endpoint].items() if value==owner);row=rows[endpoint][index]
   state=scene.graph.graph.context;base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0]
   if scene.builders is None:raise ValueError('Missing captured scenery builder')
   builder=scene.builders.at(base+owner*164,matrix_base+visit['source'][136]*48,scene.graph.refresh)
   if struct.unpack_from('<h',builder.source,54)[0]!=visit['dispatch']['model']:raise ValueError('Captured scenery builder identity mismatch')
   if projection.matrix(builder.camera,builder.source,builder.initial_matrix)!=bytes(row['blocks'][2]):raise ValueError('Captured scenery pose/source mismatch')
   blocks.append(tuple(bytes(b) for b in row['blocks']));dispatch.append(visit['dispatch'])
  if any(dispatch[0].get(k)!=dispatch[1].get(k) for k in ('model','variant','descriptor')):raise ValueError('Captured scenery identity transition')
  if any(blocks[0][i]!=blocks[1][i] for i in (1,4,5,6,7,8,10)):raise ValueError('Captured scenery topology/material transition')
  out.append(SceneryRecordPair(owner,*blocks,True,True))
 return tuple(out)
