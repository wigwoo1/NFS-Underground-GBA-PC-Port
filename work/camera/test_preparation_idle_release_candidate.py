import gc,time,weakref,json
from pathlib import Path
from owned_preparation_pipeline import PreparationPipeline as Baseline
from owned_preparation_release_candidate import PreparationPipeline as Candidate
class Token:pass
class Result:
 def close(self):self.closed=True

def check(cls):
 pipeline=cls();token=Token();token_ref=weakref.ref(token)
 def factory(token=token):return Result()
 future=pipeline.submit(factory);result=pipeline.take(future);ref=weakref.ref(result);result.close();token=factory=future=result=None
 deadline=time.monotonic()+2
 while time.monotonic()<deadline and ref() is not None:time.sleep(.01)
 gc.collect();retained=dict(factory_capture=token_ref() is not None,result=ref() is not None)
 pipeline.close();gc.collect();assert token_ref() is None and ref() is None
 return retained
old=check(Baseline);new=check(Candidate);assert old==dict(factory_capture=True,result=True) and new==dict(factory_capture=False,result=False),(old,new)
pipeline=Candidate()
try:
 def failure():raise ValueError('expected')
 f=pipeline.submit(failure)
 try:pipeline.take(f)
 except ValueError:pass
 else:raise AssertionError('Missing failure')
 f=pipeline.submit(lambda:Result());r=pipeline.take(f);r.close()
 pipeline.invalidate();f=pipeline.submit(lambda:Result());r=pipeline.take(f);r.close()
finally:pipeline.close()
out=dict(result='PASS_PREPARATION_IDLE_REFERENCE_RELEASE',baseline_idle_retained=old,candidate_idle_retained=new,failed_job_capacity_recovered=True,generation_reuse=True,scope='Real background pipeline weakrefs and lifecycle checks; does not quantify full-game memory or frame cadence.')
Path('work/camera/prototype-runs/preparation-idle-release-20261008.json').write_text(json.dumps(out,indent=2));print(out)
