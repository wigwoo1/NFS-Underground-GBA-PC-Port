import sys,json
from pathlib import Path
source=Path('work/camera/profile_captured_preparation_warm.py').read_text().split('import statistics')[0]
exec(compile(source,'captured-setup','exec'))
import owned_model_record_owners as owners
calls=[];original=owners.records
def forbidden(frame):calls.append(len(frame));raise AssertionError('Ownership reparsed an already validated endpoint')
owners.records=forbidden
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 samples=[prepared.sample(x['alpha']) for x in expected]
 actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
 assert not calls
finally:
 owners.records=original
 if prepared is not None:prepared.close()
 history.close()
print('PASS complete signatures and zero model ownership endpoint reparses')
