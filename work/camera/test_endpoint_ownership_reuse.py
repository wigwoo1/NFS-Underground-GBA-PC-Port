"""Count actual ownership resolution while running the full native regression."""
import runpy,json
from pathlib import Path
from unittest.mock import patch
import owned_external_model_owners as owners
import owned_external_record_pair as records
original=owners.external_model_owners
calls=[]
def measured(*args,**kwargs):
 calls.append((args[0].epoch,args[0].refresh))
 return original(*args,**kwargs)
with patch.object(owners,'external_model_owners',measured),patch.object(records,'external_model_owners',measured):
 runpy.run_path('work/camera/test_external_changed_parent_exit.py')
assert len(calls)==2 and len(set(calls))==2,calls
result=dict(result='PASS_TWO_ENDPOINT_RESOLUTIONS',calls=calls,scope='Complete 101-sample native4K changed-parent regression; no live speed claim')
Path('work/camera/endpoint-ownership-reuse-tests.json').write_text(json.dumps(result,indent=2));print(result)
