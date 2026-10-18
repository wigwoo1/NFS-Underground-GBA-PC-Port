import runpy,json,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_camera_scan_candidate import ClosedGraph as Candidate
calls=[0]
def match(self,frame):
 Candidate.match_frame(self,frame);calls[0]+=1
ClosedGraph.match_frame=match
runpy.run_path('work/camera/test_segmented_original_gpu_parity.py',run_name='__main__')
assert calls[0]>0,'GPU fixture did not exercise camera scanner'
p=Path(sys.argv[2]);r=json.loads(p.read_text());r['camera_scan_calls']=calls[0];p.write_text(json.dumps(r,indent=2));print('camera scanner calls',calls[0])
