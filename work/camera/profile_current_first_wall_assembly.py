import os,cProfile,pstats,json,time,hashlib
from pathlib import Path
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0]
exec(compile(setup,'actual-first-wall-setup','exec'))
import owned_sampled_world_segmented_candidate as world
import owned_continuous_wall_visibility as visibility
rows=[];reference=None
for iteration in range(8):
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
 try:
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  for fn in (visibility._ring_endpoint_corrections,visibility._sampled_ring_points,visibility._height_endpoint_terms):fn.cache_clear()
  profile=cProfile.Profile();began=time.perf_counter_ns();profile.enable()
  draws=world.sampled_graph_gpu_records(prepared.pair.portal,.01)
  profile.disable();wall_ns=time.perf_counter_ns()-began
  digest=hashlib.sha256(b''.join(x['record'] for x in draws)+repr([(x['ordinal'],x['descriptor'],x['edge'],x['bounds'],x.get('surface_phase')) for x in draws]).encode()).hexdigest()
  if reference is None:reference=digest
  assert digest==reference
  functions=[dict(file=k[0],line=k[1],name=k[2],calls=v[1],own_seconds=v[2],inclusive_seconds=v[3]) for k,v in pstats.Stats(profile).stats.items()]
  rows.append(dict(iteration=iteration,wall_ns=wall_ns,draws=len(draws),digest=digest,functions=sorted(functions,key=lambda x:x['own_seconds'],reverse=True),visibility_stages=prepared.pair.portal._last_wall_selection_stages))
 finally:
  if prepared is not None:prepared.close()
  history.close()
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/current-preparation-functions-20261010')
out=dict(result='PASS_FIRST_WALL_FUNCTION_INVENTORY',rows=rows,scope='Eight independently reconstructed capturedpair firstfraction walls with cold transform caches; exact record+order fingerprint, cProfile perturbscost and is not live performance proof.')
(folder/'first-wall-functions.json').write_text(json.dumps(out,indent=2))
print(out['result']);print(json.dumps(rows[-1]['functions'][:12],indent=2))
