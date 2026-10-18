import runpy,hashlib,ctypes as C,json
from pathlib import Path
import owned_continuous_wall_visibility as wall
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
v=runpy.run_path('work/camera/audit_failed_world_motion.py');h=EndpointRoadPlanner(v['rom'],v['data']['table']);roads,_=h.plan(v['scenes'][0].graph);p=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],h,roads,v['rom']);original=wall._sampled_ring_points
original.cache_clear()
def fingerprint(sample):
 digest=hashlib.sha256(sample[0])
 for raw in sample[1:4]:
  if raw is not None:digest.update(C.string_at(C.addressof(raw),C.sizeof(raw)))
 return digest.hexdigest()
try:
 alphas=(.1,.25,.5,.75,.9);cached=[fingerprint(p.sample(a)) for a in alphas];info=original.cache_info();assert info.hits>0 and info.currsize<=32
 wall._sampled_ring_points=original.__wrapped__
 assert [fingerprint(p.sample(a)) for a in alphas]==cached
 assert len(set(cached))==len(alphas),'Sampled scene motion held'
 print('PASS cached/uncached moving scene, pose and clip byte identity; bounded ring transforms',info)
finally:wall._sampled_ring_points=original;original.cache_clear();p.close();h.close()
a=json.loads(Path('work/camera/prototype-runs/history-transfer-benchmark-1791285993431247500.json').read_text());b=json.loads(Path('work/camera/prototype-runs/history-transfer-benchmark-1791286185869433200.json').read_text());assert a['identical_scene_fingerprint']==b['identical_scene_fingerprint'];print('PASS pre-change/post-change complete scene fingerprint')
