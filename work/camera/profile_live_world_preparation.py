"""Diagnostic preparation-thread profile; its overhead invalidates timing claims."""
import cProfile,pstats,runpy,sys,time
from pathlib import Path
from owned_preparation_pipeline import PreparationPipeline
original=PreparationPipeline._run
output=Path('work/camera/prototype-runs')/('world-preparation-'+str(time.time_ns())+'.prof')
def measured(self):
 profile=cProfile.Profile()
 try:profile.runcall(original,self)
 finally:profile.dump_stats(str(output))
PreparationPipeline._run=measured
sys.argv=['run_owned_native_prototype.py',*sys.argv[1:]]
try:runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
finally:
 PreparationPipeline._run=original
 if output.exists():
  with output.with_suffix('.txt').open('w',encoding='utf-8') as stream:pstats.Stats(str(output),stream=stream).strip_dirs().sort_stats('cumulative').print_stats(35)
  print('Diagnostic preparation profile:',output)
