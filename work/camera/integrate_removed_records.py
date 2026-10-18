from pathlib import Path
p=Path('work/camera/owned_model_record_owners.py');s=p.read_text().replace('activation={}','activation={};deactivation={}')
needle="   if record.older_allocated or not record.newer_allocated or record.object_index in maps[0].values():raise ValueError('Unverified model disappearance transition')"
replacement='''   if record.older_allocated and not record.newer_allocated and record.object_index in maps[0].values() and record.object_index not in maps[1].values():
    if newer_scene.sources is None:raise ValueError('Missing removed source closure')
    address=base+record.object_index*164;event=newer_scene.sources.removals.get(address)
    if event is None or not pair.scenes[0].graph.refresh<event[0]<=pair.scenes[1].graph.refresh or newer_scene.sources.sources[address][136]!=255:raise ValueError('Unverified source removal clock')
    deactivation[record.object_index]=(event[0]-pair.scenes[0].graph.refresh)/(pair.scenes[1].graph.refresh-pair.scenes[0].graph.refresh)
    continue
'''+needle
assert needle in s;s=s.replace(needle,replacement).replace('pair._scenery_activation=activation','pair._scenery_activation=activation;pair._scenery_deactivation=deactivation');p.write_text(s)
p=Path('work/camera/owned_sampled_model_visit.py');s=p.read_text();needle='  pair._ordinary_spatial=SpatialDescriptors(pair.scenes[0].graph)';replacement='''  if getattr(pair,'_scenery_deactivation',{}):
   from owned_removed_scenery_visit import removed_scenery_visit
   old,new=pair.portal.motion.scene_pair
   queues=[pair.portal.sample(i) for i in (0,1)]
   extra=tuple(removed_scenery_visit(old,new,*queues,index) for index in pair._scenery_deactivation)
   pair._ordinary_visit_cache=(pair._ordinary_visit_cache[0],pair._ordinary_visit_cache[1]+extra)
'''+needle
assert needle in s;s=s.replace(needle,replacement);p.write_text(s)
p=Path('work/camera/owned_sampled_world_frame.py');s=p.read_text().replace(' for index in models:\n  visit=',' for index in models:\n  if owners[index] in getattr(pair,\'_scenery_deactivation\',{}) and alpha>=pair._scenery_deactivation[owners[index]]:continue\n  visit=')
s=s.replace("if item['source_object'] in getattr(pair,'_scenery_activation',{}):","if item['source_object'] in getattr(pair,'_scenery_record_pairs',{}):");p.write_text(s)
