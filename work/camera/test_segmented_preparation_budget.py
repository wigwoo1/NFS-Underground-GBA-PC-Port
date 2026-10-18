import sys,json,ctypes as C,weakref,gc
from pathlib import Path
source=Path('work/camera/measure_captured_source_preparation_stages.py').read_text().split('import statistics')[0]
exec(compile(source,'captured_setup','exec'))
import owned_sampled_world_frame as assembly
import owned_motion_pairs as metadata
from owned_segmented_frame_candidate import SegmentedFrame
from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples
refs=[]
def join(*args):
 value=SegmentedFrame.join(*args);refs.append(weakref.ref(value));return value
assembly.join_frame=join
checks=[]
def trial(budget,expect_failure=False):
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);owner=PrecomputedSourceWorldSamples.__new__(PrecomputedSourceWorldSamples)
 before=len(refs)
 try:
  try:owner.__init__(prepared,tuple(x['alpha'] for x in expected),budget=budget,trace=True)
  except ValueError as error:
   assert expect_failure and str(error)=='Prepared source sample budget exceeded'
   assert owner.samples=={} and owner.source_masks=={} and owner.source_cameras==() and owner.bytes==0
   count=len(refs)-before;charged=None
  else:
   assert not expect_failure
   assert json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(owner.sample(x['alpha']))) for x in expected]))==expected
   charged=sum(len(sample[0].prefix)+len(sample[0].base)+sum(C.sizeof(x) for x in (*sample[1:4],*owner.source_masks[alpha][:2])) for alpha,sample in owner.samples.items())
   assert charged==owner.bytes and charged<=budget;count=len(owner.samples)
  assert prepared.history is None and prepared.next_history is None
 finally:owner.close();owner.close();prepared.close();history.close()
 # Explicitly retire the documented bounded metadata cache before auditing final reachability.
 metadata._record_cache.entries=[];gc.collect()
 assert not any(ref() is not None for ref in refs[before:]),'Closed segmented sample still retained'
 checks.append(dict(budget=budget,rejected=expect_failure,samples_attempted=count,charged_bytes=charged))
 return charged
charged=trial(64*1024*1024)
trial(1,True);trial(charged-1,True);trial(charged)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/segmented-budget-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS',checks=checks,scope='Actual captured five-source samples, exact complete signatures, conservative fullbase+prefix+array accounting, immediate/partial budgetfailure cleanup, repeatclose and final ownerweakrefs after boundedmetadata cache retirement; not live cancellation scheduling proof.')
(cp/(sys.argv[2] if len(sys.argv)>2 else 'result.json')).write_text(json.dumps(result,indent=2));print(result)
