import json,cProfile,pstats,runpy
from pathlib import Path
profile=cProfile.Profile();profile.enable()
try:runpy.run_path('work/camera/test_precomputed_source_eight_samples.py',run_name='__main__')
finally:profile.disable()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/captured-source-cpu-profile-20261007');cp.mkdir(exist_ok=True);profile.dump_stats(str(cp/'profile.pstats'))
rows=[]
for (file,line,name),(primitive,calls,self_s,cumulative_s,callers) in pstats.Stats(profile).stats.items():
 if Path(file).name.startswith(('owned_','sample_owned')) and name!='<module>':rows.append(dict(file=Path(file).name,line=line,name=name,calls=calls,self_ms=self_s*1000,cumulative_ms=cumulative_s*1000))
result=dict(result='PROFILED_PARITY_WORKLOAD',self_time=sorted(rows,key=lambda x:x['self_ms'],reverse=True)[:25],cumulative_time=sorted(rows,key=lambda x:x['cumulative_ms'],reverse=True)[:25],scope='Instrumented actual captured source preparation/parity workload; profiler adds overhead, excludes live GPU draw/HUD, not timing certification.')
(cp/'result.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result['self_time'][:8]))
