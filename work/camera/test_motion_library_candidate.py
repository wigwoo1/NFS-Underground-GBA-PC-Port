import sys,json,time
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import statistics,ctypes as C
from concurrent.futures import ThreadPoolExecutor
prior_namespace=dict(__file__=str(Path('work/camera/sample_owned_motion.py').resolve()))
exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/motion-library-reuse-20261006/before.py').read_text(),prior_namespace)
Prior=prior_namespace['PreparedMotionPair']
from owned_motion_library_candidate import PreparedMotionPair as Candidate,rigid_library
rigid_library()
a=Prior(*frames,*scenes);b=Candidate(*frames,*scenes)
for alpha in (0.,.1,.5,.9,1.):
 left=a.sample(alpha);right=b.sample(alpha)
 assert left[0]==right[0] and [None if x is None else bytes(x) for x in left[1:]]==[None if x is None else bytes(x) for x in right[1:]]
first=b.sample(.5);want=bytes(first[1]);first[1][0]+=1000
assert bytes(b.sample(.5)[1])==want
assert a.arguments[2] is not b.arguments[2]
def task(i):
 pair=Candidate(*frames,*scenes)
 result=pair.sample(.5)
 return bytes(result[1]),bytes(result[2])
with ThreadPoolExecutor(max_workers=4) as pool:
 results=list(pool.map(task,range(40)))
assert all(x==results[0] for x in results)
times={'prior':[],'candidate':[]}
for repeat in range(10):
 order=[('prior',Prior),('candidate',Candidate)]
 if repeat%2:order.reverse()
 for name,cls in order:
  begin=time.perf_counter_ns()
  for i in range(30):cls(*frames,*scenes)
  times[name].append((time.perf_counter_ns()-begin)/1e6)
result=dict(result='PASS',median_30_constructors_ms={k:statistics.median(v) for k,v in times.items()},range_ms={k:[min(v),max(v)] for k,v in times.items()},library_cache=str(rigid_library.cache_info()),scope='Exact camera/model bytes fivealphas, private mutable output and endpoint pose storage,40concurrent independent pairs; component constructor benchmark only')
Path('work/camera/motion-library-candidate-tests.json').write_text(json.dumps(result,indent=2));print(result)
