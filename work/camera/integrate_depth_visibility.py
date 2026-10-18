from pathlib import Path
p=Path('work/camera/owned_scenery_record_pairs.py');s=p.read_text().replace('removed=set()','removed=set();depth_hidden=set()')
needle="   maps[1][index]=removed_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);removed.add(index)"
replacement='''   import struct
   from owned_removed_scenery_visit import depth_hidden_scenery_visit
   source=scenes[1].sources.sources.get(struct.unpack_from('<I',scenes[1].graph.graph.context,60)[0]+index*164) if scenes[1].sources else None
   if source is not None and source[136]!=255:
    maps[1][index]=depth_hidden_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);depth_hidden.add(index)
   else:
    maps[1][index]=removed_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);removed.add(index)'''
assert needle in s;s=s.replace(needle,replacement)
needle='  if any(blocks[0][i]!=blocks[1][i]';s=s.replace(needle,"  if index in depth_hidden:blocks=(builder.prepare_visit(scenes[0],queues[0],a),builder.prepare_depth_hidden(*scenes,*queues,index))\n"+needle)
# Avoid original builder visibility call before overriding hidden result.
s=s.replace("else tuple(builder.prepare_visit(scene,queue,visit) for scene,queue,visit in zip(scenes,queues,(a,b)))","else (None,None) if index in depth_hidden else tuple(builder.prepare_visit(scene,queue,visit) for scene,queue,visit in zip(scenes,queues,(a,b)))")
p.write_text(s)
p=Path('work/camera/owned_model_record_owners.py');s=p.read_text().replace('activation={};deactivation={}','activation={};deactivation={};depth_exit=set()');needle='  for record in paired_records:'
s=s.replace(needle,needle+'''
   if record.older_allocated and record.newer_allocated and record.object_index in maps[0].values() and record.object_index not in maps[1].values():
    depth_exit.add(record.object_index);continue
''');s=s.replace('pair._scenery_deactivation=deactivation','pair._scenery_deactivation=deactivation;pair._scenery_depth_exit=depth_exit');p.write_text(s)
p=Path('work/camera/owned_sampled_model_visit.py');s=p.read_text();s=s.replace("if getattr(pair,'_scenery_deactivation',{}):","if getattr(pair,'_scenery_deactivation',{}) or getattr(pair,'_scenery_depth_exit',set()):")
s=s.replace('from owned_removed_scenery_visit import removed_scenery_visit','from owned_removed_scenery_visit import removed_scenery_visit,depth_hidden_scenery_visit')
s=s.replace("for index in pair._scenery_deactivation)","for index in pair._scenery_deactivation)+tuple(depth_hidden_scenery_visit(old,new,*queues,index) for index in pair._scenery_depth_exit)")
s=s.replace("if depth<=0:raise ValueError('Sampled ordinary model depth transition')","if depth<=0:\n  if object_index in getattr(pair,'_scenery_depth_exit',set()):return None\n  raise ValueError('Sampled ordinary model depth transition')");p.write_text(s)
p=Path('work/camera/owned_sampled_world_frame.py');s=p.read_text();needle="  visit=sampled_model_visit(pair,alpha,owners[index]);model=dict";assert needle in s;s=s.replace(needle,"  visit=sampled_model_visit(pair,alpha,owners[index])\n  if visit is None:continue\n  model=dict");p.write_text(s)
