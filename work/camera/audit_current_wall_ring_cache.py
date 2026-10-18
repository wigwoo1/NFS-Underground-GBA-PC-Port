import os,json
from pathlib import Path
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0]
exec(compile(setup,'actual-wall-ring-setup','exec'))
import owned_continuous_wall_visibility as walls
functions=[walls._ring_endpoint_corrections,walls._sampled_ring_points,walls._height_endpoint_terms]
for fn in functions:fn.cache_clear()
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;rows=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 for alpha in (.01,.2,.4,.6,.8,.99):
  before=[fn.cache_info() for fn in functions];prepared.sample(alpha);after=[fn.cache_info() for fn in functions]
  rows.append(dict(alpha=alpha,caches=[dict(name=fn.__name__,hits=b.hits-a.hits,misses=b.misses-a.misses,size=b.currsize,capacity=b.maxsize) for fn,a,b in zip(functions,before,after)]))
finally:
 if prepared is not None:prepared.close()
 history.close()
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/current-preparation-functions-20261010')
out=dict(result='PASS_ACTUAL_WALL_RING_CACHE_INVENTORY',rows=rows,scope='Actual capturedpair sixfractions currentwall assembly; caches cleared initially, counts do not bythemselves prove time benefit or live behavior.')
(folder/'wall-ring-cache.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
