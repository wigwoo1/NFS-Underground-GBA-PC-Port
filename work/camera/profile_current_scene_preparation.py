import os,cProfile,pstats,json,time
from pathlib import Path
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0]
exec(compile(setup,'current-captured-pair','exec'))
profile=cProfile.Profile();rows=[]
try:
 for iteration in range(4):
  profile=cProfile.Profile()
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
  prepared=samples=None
  try:
   profile.enable();began=time.perf_counter_ns()
   prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
   samples=ProgressiveSourceWorldSamples(prepared,(.01,.2,.4,.6,.8,.99),trace=True)
   profile.disable()
   assert len(samples.samples)==6
   functions=[dict(file=k[0],line=k[1],name=k[2],calls=v[1],own_seconds=v[2],inclusive_seconds=v[3]) for k,v in pstats.Stats(profile).stats.items()]
   rows.append(dict(iteration=iteration,wall_ns=time.perf_counter_ns()-began,sample_timings=samples.sample_timings,functions_by_own_time=sorted(functions,key=lambda x:x['own_seconds'],reverse=True)))
  finally:
   profile.disable()
   if samples is not None:samples.close()
   if prepared is not None:prepared.close()
   history.close()
finally:profile.disable()
stats=pstats.Stats(profile)
functions=[dict(file=k[0],line=k[1],name=k[2],primitive_calls=v[0],calls=v[1],own_seconds=v[2],inclusive_seconds=v[3]) for k,v in stats.stats.items()]
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/current-preparation-functions-20261010');folder.mkdir(exist_ok=True)
profile.dump_stats(str(folder/'preparation.prof'))
out=dict(result='PASS_CURRENT_PREPARATION_FUNCTION_INVENTORY',preparations=4,samples=24,last_preparation_functions_by_own_time=sorted(functions,key=lambda x:x['own_seconds'],reverse=True),preparation_rows=rows,scope='Four actual captured-pair full preparations with six fractions, diagnostic cProfile perturbs time; not live cadence or performance comparison.')
(folder/'profile.json').write_text(json.dumps(out,indent=2))
print(out['result'])
print(json.dumps(out['preparation_rows'][-1]['functions_by_own_time'][:12],indent=2))
