import runpy,time,statistics
from pathlib import Path
candidate={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/wall-record-template-cache-20261006/candidate.py').read_text(),candidate);sampled_graph_gpu_records=candidate['sampled_graph_gpu_records']
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
v=runpy.run_path('work/camera/profile_world_construction.py');scenes=v['v']['scenes'];motion=PreparedMotionPair(*v['data']['frames'],*scenes);portal=PortalMotionPair(scenes[0].graph.graph,scenes[1].graph.graph,v['data']['table'],motion)
namespace={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/wall-record-template-cache-20261006/before.py').read_text(),namespace);before=namespace['sampled_graph_gpu_records'];times={before:[],sampled_graph_gpu_records:[]}
for i in range(101):
 alpha=i/100;out={}
 for fn in ((before,sampled_graph_gpu_records) if i%2==0 else (sampled_graph_gpu_records,before)):
  start=time.perf_counter_ns();out[fn]=fn(portal,alpha);times[fn].append(time.perf_counter_ns()-start)
 assert out[before]==out[sampled_graph_gpu_records]
assert len(portal._wall_record_templates)<=512
print('PASS101 byteexact wall records/order/clips beforeafter; medianms',*[round(statistics.median(times[f])/1e6,3) for f in (before,sampled_graph_gpu_records)])
