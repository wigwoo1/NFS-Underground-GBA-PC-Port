import runpy,hashlib,ctypes as C
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
v=runpy.run_path('work/camera/audit_failed_world_motion.py');h=EndpointRoadPlanner(v['rom'],v['data']['table']);roads,_=h.plan(v['scenes'][0].graph);p=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],h,roads,v['rom'])
def fingerprint(sample):
 digest=hashlib.sha256(sample[0])
 for raw in sample[1:4]:
  if raw is not None:digest.update(C.string_at(C.addressof(raw),C.sizeof(raw)))
 return digest.hexdigest()
try:
 alphas=(.1,.25,.5,.75,.9);cached=[fingerprint(p.sample(a)) for a in alphas];cache=p.pair._supplemental_projection_inputs
 assert cache[0] is v['rom'] and 0<len(cache[1])<=len({w.descriptor for w in p.pair.assets[0]})
 assert len(set(cached))==len(alphas),'Sampled motion was held'
 for a,expected in zip(alphas,cached):
  if hasattr(p.pair,'_supplemental_projection_inputs'):del p.pair._supplemental_projection_inputs
  assert fingerprint(p.sample(a))==expected,'Projection input reuse changed frame/pose/clips'
 print('PASS five moving samples byte-identical with and without bounded source-owned projection reuse')
finally:p.close();h.close()
