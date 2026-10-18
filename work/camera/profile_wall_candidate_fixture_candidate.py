from pathlib import Path
import sys,cProfile,pstats,json
sys.path.insert(0,str(Path('work/camera').resolve()))
env={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),env)
prof=cProfile.Profile();history,prepared=env['prepare']()
try:
 prof.enable();samples=env['ProgressiveSourceWorldSamples'](prepared,env['alphas']);prof.disable();samples.close()
finally:history.close()
stats=pstats.Stats(prof);rows=[]
for (filename,line,name),(cc,nc,tt,ct,callers) in stats.stats.items():
 if ct>.00002 or name=='validate':
  rows.append(dict(file=filename,line=line,name=name,primitive_calls=cc,calls=nc,self_seconds=tt,cumulative_seconds=ct,callers=[dict(file=k[0],line=k[1],name=k[2],metrics=list(v) if isinstance(v,tuple) else v) for k,v in callers.items()]))
rows.sort(key=lambda x:x['cumulative_seconds'],reverse=True)
out=dict(result='OBSERVED_COMPLETE_FIXTURE_WALL_PROFILE',rows=rows,scope='One complete saved-fixture six-sample cProfile; profiling perturbs runtime, cumulative parents overlap. No live performance or fullscene fidelity claim.')
Path('outputs/nfsug-native-renderer/camera-research/wall-candidate-fixture-profile-20261009.json').write_text(json.dumps(out,indent=2))
for row in rows:
 if any(c['name']=='wall_region_candidates' for c in row['callers']):print(row)
