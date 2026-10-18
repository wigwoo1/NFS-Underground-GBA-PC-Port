import sys,json,inspect,pickle
from pathlib import Path
import test_request_release_process_4k_candidate
import owned_child_request_release_install_candidate
import owned_endpoint_reference_process_service_candidate as base
from owned_scene_process_transport import pack
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'release-liveness-fixture','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom=[ns[k] for k in ('frames','scenes','rom')]
class Connection:
 def __init__(self):self.calls=0;self.responses=[];self.checked=False
 def recv(self):
  self.calls+=1
  if self.calls==1:return (1,pack(frames[0],scenes[0]),scenes[0].identity,pack(frames[1],scenes[1]),(.1,.35,.9))
  local=inspect.currentframe().f_back.f_locals
  for name in ('a','sa','b','sb','encoded','samples','sidecar','construct_trace','sample_trace','encode_trace'):assert local[name] is None,name
  assert local['previous'][1].identity==scenes[1].identity and local['history'] is not None
  self.checked=True;return None
 def send(self,value):self.responses.append(pickle.loads(pickle.dumps(value)))
 def close(self):pass
connection=Connection();base.reference_child(connection,rom,None)
assert connection.checked and len(connection.responses)==2 and connection.responses[0][0]=='ok'
out=dict(result='PASS_ACTUAL_CHILD_COMPLETED_REQUEST_LOCAL_RELEASE',released_locals=10,result_and_trace_copied=True,previous_scene_and_history_retained=True)
Path('work/camera/prototype-runs/child-request-release-liveness-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
