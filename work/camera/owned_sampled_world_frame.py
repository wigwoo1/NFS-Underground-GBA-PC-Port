from owned_double_array_type import double_array_type
"""Full sampled main surfaces plus supplemental walls and retained car anchor."""
import struct,ctypes as C,time
from owned_thread_cycles import read as thread_cycles
from owned_motion_pairs import records
from owned_sampled_model_visit import sampled_model_visit
from owned_model_record_owners import model_record_owners
from owned_scene_bundle import chunks
from owned_sampled_supplemental_frame import encode
from owned_sampled_graph_gpu import sampled_graph_gpu_records
from owned_complete_supplemental_gpu import sampled_gpu_records

def join_frame(header,geometry,base,tailoffset):
 return b''.join((header,*geometry,memoryview(base)[tailoffset:]))

def assemble_world(pair,roads,endpoint_roads,alpha,rom):
 stages=[];pair._last_sample_stages=stages;start=time.perf_counter_ns();cycles_start=thread_cycles();cpu_start=time.thread_time_ns()
 def stage(name):
  nonlocal start,cycles_start,cpu_start
  cpu_end=time.thread_time_ns();end=time.perf_counter_ns();cycles=thread_cycles();stages.append(dict(name=name,started_ns=start,completed_ns=end,wall_ns=end-start,thread_cycles=cycles-cycles_start,thread_cpu_ns=cpu_end-cpu_start));start=end;cycles_start=cycles;cpu_start=cpu_end
 base,camera,old_models=pair.portal.motion.sample(alpha)
 motion=pair.portal.motion;plan=motion.arguments[0]
 # The validated motion plan already owns both immutable endpoint record sets.
 if base is motion.older:rows=list(plan['older']['records'])
 elif base is motion.newer:rows=list(plan['newer']['records'])
 else:raise ValueError('Sample frame is outside the owned motion endpoints')
 models=[i for i,r in enumerate(rows) if r['kind']==3]
 if not models or any(r['kind'] not in (1,2,3) for r in rows):raise ValueError('Unverified ordinary object anchor')
 stage('motion_and_anchors')
 if alpha in (0,1):
  # Preserve every original endpoint draw, including retained surface records
  # unavailable to a cold reconstruction history. Intermediates still rebuild.
  model_record_owners(pair,rom)
  supplemental_keys={item.vertices for item in pair.assets[int(alpha)]}
  supplemental_count=sum(r['kind']==2 and bytes(r['blocks'][0]) in supplemental_keys for r in rows)
  return base,None,None,double_array_type(4*len(rows))(),dict(main_walls=sum(r['kind']==2 for r in rows)-supplemental_count,roads=sum(r['kind']==1 for r in rows),supplemental_walls=supplemental_count,model_anchor='source-owned original endpoint',geometry_records=len(rows))

 main=sampled_graph_gpu_records(pair.portal,alpha);stage('main_graph_surfaces');stages[-1]['visibility_stages']=getattr(pair.portal,'_last_wall_selection_stages',[])
 if getattr(pair.portal,'_last_sampled_graph_stages',None) is not None:stages[-1]['sampled_graph_stages']=pair.portal._last_sampled_graph_stages
 road_records=endpoint_roads[int(alpha)] if alpha in (0,1) else roads.sample(alpha)[0]
 stage('sampled_roads');stages[-1]['road_stages']=getattr(roads,'_last_road_stages',[]);stages[-1]['road_stage_dropped']=getattr(roads,'_road_stage_dropped',0)
 main=tuple(main)+tuple(getattr(roads,'child_walls',()))
 surfaces=[((-x['ordinal'],x.get('static_depth',0),x.get('surface_phase',0),x['edge']),x) for x in main]+[((-x['ordinal'],x.get('static_depth',0),1,x['secondary']),x) for x in road_records]
 ordered=[x for _,x in sorted(surfaces,key=lambda x:x[0])];stage('surface_order')
 supp=sampled_gpu_records(pair,alpha,rom);stage('supplement_surfaces')
 owner_maps=model_record_owners(pair,rom);owners=dict(owner_maps[1 if alpha==1 else 0]);stage('model_owners');stages[-1]['owner_stages']=getattr(pair,'_model_owner_stages',[])
 if 0<alpha<1 and hasattr(pair,'_scenery_activation'):
  newer_rows=plan['newer']['records']
  for index,owner in owner_maps[1].items():
   if owner not in pair._scenery_activation or alpha<pair._scenery_activation[owner]:continue
   if owner in owners.values():continue
   source_pair=pair._scenery_record_pairs[owner];rows.append(dict(newer_rows[index],blocks=source_pair.older_blocks));new_index=len(rows)-1;models.append(new_index);owners[new_index]=owner
 if not hasattr(pair,'_chain_positions'):
  from types import MappingProxyType
  maps=[]
  for scene in pair.scenes:
   positions={}
   for header,raw in chunks(scene.objects,'graph_objects'):
    for i in range(header[5]):positions[(header[3],struct.unpack_from('<I',raw,128+i*168)[0])]=i
   maps.append(MappingProxyType(positions))
  pair._chain_positions=tuple(maps)
 positions=pair._chain_positions[1 if alpha==1 else 0]
 objects=[( (-x['ordinal'],-x['distance'],-positions[(x['parent'],x['object'])]),x) for x in supp]
 for index in models:
  if owners[index] in getattr(pair,'_scenery_deactivation',{}) and alpha>=pair._scenery_deactivation[owners[index]]:continue
  visit=sampled_model_visit(pair,alpha,owners[index])
  if visit is None:continue
  row=rows[index]
  if owners[index] in getattr(pair,'_external_visits',{}):
   blocks=list(row['blocks']);left,right,top,bottom=visit['bounds'];blocks[9]=struct.pack('<4i',*(round(v) for v in (left,top,right,bottom)));row=dict(row,blocks=blocks)
  model_rect=struct.unpack('<4i',row['blocks'][9]);model_bounds=(model_rect[0],model_rect[2],model_rect[1],model_rect[3])
  if owners[index] in getattr(pair,'_external_visits',{}):model_bounds=tuple(visit['bounds'])
  # Ordinary immutable endpoint model bytes do not depend on sampled pose.
  # External/scenery records retain their per-sample encoding and guards.
  if owners[index] not in getattr(pair,'_external_visits',{}) and owners[index] not in getattr(pair,'_scenery_record_pairs',{}):
   if not hasattr(pair,'_ordinary_encoded_models'):pair._ordinary_encoded_models={}
   key=(0 if base is motion.older else 1,index)
   cache=pair._ordinary_encoded_models
   if key not in cache:cache[key]=encode(row)
   encoded_model=cache[key]
  else:encoded_model=encode(row)
  model=dict(record=encoded_model,bounds=model_bounds,model=index,source_object=owners[index])
  objects.append(((-visit['ordinal'],-visit['distance'],-visit['position']),model))
 ordered += [x for _,x in sorted(objects,key=lambda x:x[0])]
 stage('object_visits_and_order')
 geometry=[x['record'] for x in ordered];bounds=[v for x in ordered for v in x['bounds']]
 stage('geometry_and_bounds_lists')
 h=list(struct.unpack_from('<6I2Q',base));h[2]=sum(map(len,geometry));tailoffset=40+struct.unpack_from('<I',base,8)[0];frame=join_frame(struct.pack('<6I2Q',*h),geometry,base,tailoffset);new_models=None
 stage('immutable_frame_join');stages[-1].update(geometry_bytes=h[2],tail_bytes=len(base)-tailoffset,frame_bytes=len(frame),geometry_records=len(geometry))
 if globals().get('join_frame_trace') is not None:stages[-1]['frame_join_trace']=join_frame_trace()
 if old_models is not None:
  new_models=double_array_type(12*len(geometry))()
  for index,item in enumerate(ordered):
   if 'model' in item:
    if item['source_object'] in getattr(pair,'_scenery_record_pairs',{}):
     values=pair._scenery_motion.matrix(item['source_object'],alpha)
     for k in range(12):new_models[index*12+k]=values[k]
    else:
     for k in range(12):new_models[index*12+k]=old_models[item['model']*12+k]
 stage('model_array_encoding');stages[-1]['model_array_bytes']=0 if new_models is None else C.sizeof(new_models)
 encoded_bounds=double_array_type(len(bounds))(*bounds)
 stage('bounds_array_encoding');stages[-1]['bounds_array_bytes']=C.sizeof(encoded_bounds)
 return frame,camera,new_models,encoded_bounds,dict(main_walls=len(main),roads=len(road_records),supplemental_walls=len(supp),model_anchor='source-owned ordinary car portal visit',geometry_records=len(geometry))


