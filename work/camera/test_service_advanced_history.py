import runpy
from owned_world_preparation_service import WorldPreparationService
from owned_endpoint_road_planner import EndpointRoadPlanner
v=runpy.run_path('work/camera/audit_failed_world_motion.py');calls=[];original=EndpointRoadPlanner.plan
def counted(self,scene,*args,**kwargs):
 calls.append(scene.refresh);return original(self,scene,*args,**kwargs)
EndpointRoadPlanner.plan=counted;service=WorldPreparationService(v['rom'],2);prepared=None
try:
 future=service.submit((v['data']['frames'][0],v['scenes'][0]),(v['data']['frames'][1],v['scenes'][1]));prepared=service.take(future)
 assert calls==[s.graph.refresh for s in v['scenes']],calls
 assert service.history.refresh==v['scenes'][1].graph.refresh and prepared.next_history is None
 retained=service.history;prepared.close();prepared=None;assert retained.scratch
 service.invalidate();calls.clear()
 future=service.submit((v['data']['frames'][0],v['scenes'][0]),(v['data']['frames'][1],v['scenes'][1]));prepared=service.take(future)
 assert calls==[s.graph.refresh for s in v['scenes']] and not retained.scratch
 assert prepared.sample(0)[0]==v['data']['frames'][0]
 retained=service.history;prepared.close();prepared=None;service.close();assert not retained.scratch
 print('PASS two source road plans per interval, history transfer, generation reset and independent cleanup')
finally:
 if prepared:prepared.close()
 service.close();EndpointRoadPlanner.plan=original
