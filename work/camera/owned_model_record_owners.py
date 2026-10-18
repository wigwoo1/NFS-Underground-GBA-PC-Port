"""Model record ownership through unique raw descriptor/source identity."""
from owned_motion_pairs import records
from owned_ordinary_model_visits import ordinary_model_visits

def endpoint_model_record_owners(scene,visits,frame,rom,owned_scene=None,external_owners=None,decoded_rows=None):
 """Resolve shared car meshes by exact original external builder pose first."""
 from owned_external_model_owners import external_model_owners
 external=external_owners if external_owners is not None else external_model_owners(scene,owned_scene.builders,frame,rom,decoded_rows=decoded_rows) if owned_scene is not None and owned_scene.builders is not None and any(b.external_enabled for values in owned_scene.builders.records.values() for b in values) else {}
 mapping={}
 for index,row in enumerate(records(frame)['records'] if decoded_rows is None else decoded_rows):
  if row['kind']!=3:continue
  if index in external:
   mapping[index]=external[index]
   continue
  matches=[]
  for visit in visits:
   if visit['object'] in external.values():continue
   # An external source can remain in the chain without an emitted model draw.
   # It must not compete with the ordinary player merely because the mesh is shared.
   import struct
   if struct.unpack_from('<H',visit['source'],10)[0]&32:
    if owned_scene is None or owned_scene.builders is None:raise ValueError('Missing absent external builder ownership')
    base=struct.unpack_from('<I',scene.graph.context,60)[0]
    known=[b for (address,_),values in owned_scene.builders.records.items() if address==base+visit['object']*164 for b in values if b.refresh<=scene.refresh and b.external_enabled and b.source[54:56]==visit['source'][54:56] and b.source[140:144]==visit['source'][140:144]]
    if not known:raise ValueError('Unverified absent external source identity')
    continue
   address=visit['dispatch']['descriptor']-0x08000000
   if 0<=address<=len(rom)-40 and bytes(row['blocks'][1])==rom[address:address+40]:matches.append(visit['object'])
  if len(matches)>1:
   import struct
   from owned_scenery_projection import SceneryProjection
   if owned_scene is None or owned_scene.builders is None:raise ValueError('Missing duplicate model builder ownership')
   state=scene.graph.context[:256];base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0];projection=SceneryProjection(rom);exact=[]
   for owner in matches:
    visit=next(v for v in visits if v['object']==owner)
    if not 30<=visit['dispatch']['model']<=36:raise ValueError('Unverified duplicate model kind')
    builder=owned_scene.builders.at(base+owner*164,matrix_base+visit['source'][136]*48,scene.refresh)
    matrix=projection.matrix(builder.camera,builder.source,builder.initial_matrix)
    if matrix==bytes(row['blocks'][2]):exact.append(owner)
   matches=exact
  if len(matches)!=1:raise ValueError('Ambiguous or missing source model record owner')
  mapping[index]=matches[0]
 if len(set(mapping.values()))!=len(mapping):raise ValueError('Repeated source model record owner')
 return mapping

def model_record_owners(pair,rom):
 if hasattr(pair,'_model_record_owners'):return pair._model_record_owners
 import time
 from owned_thread_cycles import read as thread_cycles
 timings=[];started=time.perf_counter_ns();cycles=thread_cycles()
 def stage(name):
  nonlocal started,cycles
  now=time.perf_counter_ns();current=thread_cycles()
  timings.append(dict(name=name,started_ns=started,completed_ns=now,wall_ns=now-started,thread_cycles=current-cycles))
  started=now;cycles=current
 pair._model_owner_stages=timings
 maps=[];endpoint_external=[]
 for endpoint,scene in enumerate(pair.scenes):
  visits=ordinary_model_visits(scene,pair.portal.sample(endpoint));frame=pair.portal.motion.older if endpoint==0 else pair.portal.motion.newer;mapping={}
  owned_scene=pair.portal.motion.scene_pair[endpoint] if pair.portal.motion.scene_pair else None
  from owned_external_model_owners import external_model_owners
  decoded_rows=pair.portal.motion.arguments[0]['older' if endpoint==0 else 'newer']['records']
  external_map=external_model_owners(scene,owned_scene.builders,frame,rom,decoded_rows=decoded_rows) if owned_scene is not None and owned_scene.builders is not None and any(b.external_enabled for values in owned_scene.builders.records.values() for b in values) else {}
  endpoint_external.append(external_map)
  mapping=endpoint_model_record_owners(scene,visits,frame,rom,owned_scene,external_map,decoded_rows)
  maps.append(mapping);stage("endpoint_"+str(endpoint))
 paired=dict(pair.portal.motion.arguments[0]['pairs'])
 changed=set(maps[0].values())^set(maps[1].values())
 persistent_unpaired={owner for index,owner in maps[0].items() if owner in maps[1].values() and maps[1].get(paired.get(index))!=owner}
 external={owner for mapping in endpoint_external for owner in mapping.values()}
 required=changed|persistent_unpaired|external
 stage("transition_classification")
 if required:
  motion=pair.portal.motion
  if motion.scene_pair is None:raise ValueError('Unverified model birth/death transition')
  from owned_scenery_record_pairs import prepare_scenery_record_pairs,captured_scenery_record_pairs
  from owned_scenery_motion import PreparedSceneryMotion
  import struct
  stage("scenery_owner_modules_import")
  queue_samples=[];queues=[]
  for endpoint in (0,1):
   queue_started=time.perf_counter_ns();queue_cycles=thread_cycles()
   queues.append(pair.portal.sample(endpoint))
   queue_samples.append(dict(endpoint=endpoint,wall_ns=time.perf_counter_ns()-queue_started,thread_cycles=thread_cycles()-queue_cycles))
  stage("source_render_queue_samples")
  timings[-1]["samples"]=queue_samples
  scenery_changed=changed-external;scenery_persistent=persistent_unpaired-external 
  player_persistent=scenery_persistent & {0};scenery_persistent-=player_persistent
  scenery_builds=[]
  if scenery_changed:
   build_started=time.perf_counter_ns();build_cycles=thread_cycles()
   owner_costs=[]
   paired_records=prepare_scenery_record_pairs(motion.scene_pair,queues,rom,scenery_changed,timing=owner_costs)
   scenery_builds.append(dict(kind="changed",owners=sorted(scenery_changed),wall_ns=time.perf_counter_ns()-build_started,thread_cycles=thread_cycles()-build_cycles,records=len(paired_records),owner_costs=owner_costs))
  else:paired_records=()
  if scenery_persistent:
   build_started=time.perf_counter_ns();build_cycles=thread_cycles()
   captured=captured_scenery_record_pairs(motion.scene_pair,queues,(motion.older,motion.newer),maps,rom,scenery_persistent,decoded_rows=[motion.arguments[0][key]['records'] for key in ('older','newer')])
   scenery_builds.append(dict(kind="captured_persistent",owners=sorted(scenery_persistent),wall_ns=time.perf_counter_ns()-build_started,thread_cycles=thread_cycles()-build_cycles,records=len(captured)))
   paired_records+=captured
  from owned_scenery_record_pairs import SceneryRecordPair
  for owner in player_persistent:
   endpoint_blocks=[]
   for endpoint,frame in enumerate((motion.older,motion.newer)):
    visit=next(v for v in ordinary_model_visits(pair.scenes[endpoint],queues[endpoint]) if v['object']==owner)
    if visit['dispatch']['model']!=7:raise ValueError('Unverified persistent player model')
    row_index=next(i for i,value in maps[endpoint].items() if value==owner)
    endpoint_blocks.append(tuple(bytes(b) for b in motion.arguments[0]['older' if endpoint==0 else 'newer']['records'][row_index]['blocks']))
   if any(endpoint_blocks[0][k]!=endpoint_blocks[1][k] for k in (1,4,5,6,7,8)):raise ValueError('Persistent player topology changed')
   # Texture bytes are discrete endpoint material state, not mesh topology.
   # Intermediates retain the older scene material; alpha=1 is the exact newer frame.
   if len(endpoint_blocks[0][10])!=len(endpoint_blocks[1][10]) or endpoint_blocks[0][0][56:60]!=endpoint_blocks[1][0][56:60]:raise ValueError('Persistent player texture layout changed')
   paired_records+=(SceneryRecordPair(owner,*endpoint_blocks,True,True),)
  stage("scenery_record_pairs")
  timings[-1].update(changed_owner_count=len(scenery_changed),persistent_owner_count=len(scenery_persistent),player_persistent_count=len(player_persistent),builds=scenery_builds)
  from owned_external_record_pair import prepare_external_record_pair
  stage("external_record_module_import")
  external_visits={};external_activation={};external_pair_costs=[]
  for owner in sorted(external):
   owner_started=time.perf_counter_ns();owner_cycles=thread_cycles()
   record,visit,start=prepare_external_record_pair(motion.scene_pair,queues,(motion.older,motion.newer),rom,owner,endpoint_external)
   paired_records+=(record,);external_visits[owner]=visit
   if start is not None:external_activation[owner]=start
   external_pair_costs.append(dict(owner=owner,wall_ns=time.perf_counter_ns()-owner_started,thread_cycles=thread_cycles()-owner_cycles,records=1,activation_start=start))
  stage("external_record_pairs")
  timings[-1].update(external_owner_count=len(external),owner_costs=external_pair_costs,total_paired_record_count=len(paired_records))
  pair._external_visits=external_visits
  activation=dict(external_activation);deactivation={};depth_exit=set();portal_exit=set();far_exit=set()
  newer_scene=motion.scene_pair[1];state=newer_scene.graph.graph.context[:256];base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0]
  newer_visits={v['object']:v for v in ordinary_model_visits(newer_scene.graph,pair.portal.sample(1),True)}
  for record in paired_records:
   if record.object_index in external:continue
   if record.object_index in persistent_unpaired:
    if not record.older_allocated or not record.newer_allocated:raise ValueError('Unverified persistent scenery allocation')
    continue
   if record.older_allocated and record.newer_allocated and record.object_index in maps[0].values() and record.object_index not in maps[1].values():
    raw=newer_scene.sources.sources[base+record.object_index*164]
    from owned_object_filter import depth_distance
    depth=depth_distance(raw,newer_scene.graph.graph.context[256:304])[0]
    if depth>=8192:
     if not struct.unpack_from('<H',raw,10)[0]&2 or record.object_index not in newer_visits:raise ValueError('Unverified far-exit scenery source')
     far_exit.add(record.object_index)
    elif depth>0:portal_exit.add(record.object_index)
    else:depth_exit.add(record.object_index)
    continue

   if record.older_allocated and not record.newer_allocated and record.object_index in maps[0].values() and record.object_index not in maps[1].values():
    if newer_scene.sources is None:raise ValueError('Missing removed source closure')
    address=base+record.object_index*164;event=newer_scene.sources.removals.get(address)
    if event is None or not pair.scenes[0].graph.refresh<event[0]<=pair.scenes[1].graph.refresh or newer_scene.sources.sources[address][136]!=255:raise ValueError('Unverified source removal clock')
    deactivation[record.object_index]=(event[0]-pair.scenes[0].graph.refresh)/(pair.scenes[1].graph.refresh-pair.scenes[0].graph.refresh)
    continue
   if record.older_allocated or not record.newer_allocated or record.object_index in maps[0].values():raise ValueError('Unverified model disappearance transition')
   visit=newer_visits[record.object_index]
   builder=newer_scene.builders.at(base+record.object_index*164,matrix_base+visit['source'][136]*48,newer_scene.graph.refresh)
   refresh=builder.refresh
   # Builder inputs precede page-flip publication. Map the owned source
   # interval onto displayed scenes without advancing render latency.
   old_refresh=pair.scenes[0].graph.refresh;new_refresh=pair.scenes[1].graph.refresh
   if not old_refresh<refresh<=new_refresh:raise ValueError('Model allocation time outside motion interval')
   activation[record.object_index]=(refresh-old_refresh)/(new_refresh-old_refresh)
  pair._scenery_record_pairs={r.object_index:r for r in paired_records}
  pair._scenery_activation=activation;pair._scenery_deactivation=deactivation;pair._scenery_depth_exit=depth_exit;pair._scenery_portal_exit=portal_exit;pair._scenery_far_exit=far_exit
  pair._scenery_motion=PreparedSceneryMotion(paired_records,pair.scenes[0].graph.context[256:304],pair.scenes[1].graph.context[256:304])
 stage("scenery_activation_and_motion")
 for index,owner in maps[0].items():
  if owner not in maps[1].values():continue
  if owner in persistent_unpaired or owner in external:continue
  if index not in paired or maps[1].get(paired[index])!=owner:raise ValueError('Model pose/source identity mismatch')
 from types import MappingProxyType
 pair._model_record_owners=tuple(MappingProxyType(m) for m in maps)
 stage("owner_publication")
 return pair._model_record_owners
