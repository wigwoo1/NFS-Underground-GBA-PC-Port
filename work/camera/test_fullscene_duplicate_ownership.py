import runpy
from owned_motion_scene import MotionScene
from owned_closed_supplements import ClosedSupplements
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_model_builder_inputs import OwnedModelBuilders
from owned_motion_pairs import records
v=runpy.run_path('work/camera/test_duplicate_model_source_ownership.py');data=v['v']['v'];scenes=[]
for endpoint,closed in enumerate(data['scenes']):
 builders=OwnedModelBuilders((data['folder']/(('older','newer')[endpoint]+'.builders.bin')).read_bytes())
 scenes.append(MotionScene(closed,ClosedSupplements.decode((data['folder']/((('older','newer')[endpoint])+'.supplements.bin')).read_bytes(),closed,v['v']['rom']),builders,data['sources'][endpoint]))
history=EndpointRoadPlanner(v['v']['rom'],data['table']);roads,_=history.plan(scenes[0].graph)
prepared=PreparedWorldMotion(*data['frames'],*scenes,history,roads,v['v']['rom']);counts=[]
try:
 for alpha in (0,.1,.25,.5,.75,.9,.99,1):
  frame,*_=prepared.sample(alpha);counts.append(sum(r['kind']==3 for r in records(frame)['records']))
  if alpha in (0,1):assert frame==data['frames'][int(alpha)]
 assert prepared.pair._scenery_activation.keys()=={54}
 assert 33 in prepared.pair._scenery_record_pairs
 pair=prepared.pair._scenery_record_pairs[33]
 for endpoint,blocks in enumerate((pair.older_blocks,pair.newer_blocks)):
  mapping=prepared.pair._model_record_owners[endpoint]
  index=next(i for i,owner in mapping.items() if owner==33)
  actual=records(data['frames'][endpoint])['records'][index]['blocks']
  assert blocks[2]==bytes(actual[2]),'Persistent source pose differs from original draw'
 assert len({prepared.pair._scenery_motion.matrix(33,i/100) for i in range(101)})==101
 assert counts[0]==3 and counts[-1]==4,counts
 print('PASS duplicate model source world assembly, exact endpoints and independently sampled persistent source',counts)
finally:prepared.close();history.close()
