from pathlib import Path
p=Path('work/camera/owned_model_record_builder.py');s=p.read_text();needle=' def prepare_visit(self,scene,queue,visit):\n';assert needle in s
s=s.replace(needle,''' def prepare_removed(self,older,newer,old_queue,new_queue,index):
  from owned_removed_scenery_visit import removed_scenery_visit
  visit=removed_scenery_visit(older,newer,old_queue,new_queue,index)
  return self._prepare(newer,new_queue,visit,False)
 def prepare_visit(self,scene,queue,visit):return self._prepare(scene,queue,visit,True)
 def _prepare(self,scene,queue,visit,require_chain):
''')
s=s.replace("if not any(all(v[k]==visit[k]", "if require_chain and not any(all(v[k]==visit[k]")
p.write_text(s)
p=Path('work/camera/owned_scenery_record_pairs.py');s=p.read_text();needle=" if len(maps)!=2:raise ValueError('Incomplete scenery record pair')";assert needle in s
s=s.replace(needle,needle+'''
 removed=set()
 if object_indices is not None:
  from owned_removed_scenery_visit import removed_scenery_visit
  for index in set(object_indices)&maps[0].keys()-maps[1].keys():
   maps[1][index]=removed_scenery_visit(scenes[0],scenes[1],queues[0],queues[1],index);removed.add(index)
''')
s=s.replace("blocks=tuple(builder.prepare_visit(scene,queue,visit) for scene,queue,visit in zip(scenes,queues,(a,b)))","blocks=(builder.prepare_visit(scenes[0],queues[0],a),builder.prepare_removed(*scenes,*queues,index)) if index in removed else tuple(builder.prepare_visit(scene,queue,visit) for scene,queue,visit in zip(scenes,queues,(a,b)))")
p.write_text(s)
