from pathlib import Path
import sys,json,time,hashlib,statistics
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
import owned_source_presentation_batch_candidate as source_batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
source_batch.SourceFaceDeterminants=SourceFaceDeterminants
import owned_portal_traversal as original
from owned_portal_point_cache_candidate import traverse as candidate
base=original.traverse.__code__;changed=candidate.__code__;alphas=(.01,.2,.4,.6,.8,.99);rows=[]
manifest=json.loads(Path('outputs/nfsug-native-renderer/camera-research/captured-pair-adjacency-20261009.json').read_text())
folders=[x['folder'] for x in manifest['pairs'][:3]]+['work/camera/prototype-runs/fullscene-failure-1791576492416199100']
setup=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('history=EndpointRoadPlanner')[0]
for folder in folders:
 ns={};exec(setup.replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(folder)+')'),ns)
 results=[]
 for i in range(8):
  hashes={};timings={}
  for label,code in ([('baseline',base),('candidate',changed)] if i%2==0 else [('candidate',changed),('baseline',base)]):
   original.traverse.__code__=code;history=EndpointRoadPlanner(ns['rom'],ns['table']);roads,_=history.plan(ns['scenes'][0].graph);prepared=None;samples=None;packets=[]
   try:
    prepared=PreparedWorldMotion(*ns['frames'],*ns['scenes'],history,roads,ns['rom'])
    started=time.perf_counter_ns();samples=ProgressiveSourceWorldSamples(prepared,alphas,on_sample=packets.append);timings[label]=time.perf_counter_ns()-started
    hashes[label]=[hashlib.sha256(bytes(p[1])+b''.join(p[2:7])+repr(p[7:]).encode()).hexdigest() for p in packets]
   finally:
    if samples:samples.close()
    if prepared:prepared.close()
    history.close()
  assert hashes['baseline']==hashes['candidate'] and len(hashes['candidate'])==6
  results.append(timings)
 rows.append(dict(folder=folder,identities=[list(s.identity) for s in ns['scenes']],pairs=8,median_ms={k:statistics.median(x[k] for x in results)/1e6 for k in ['baseline','candidate']},timings=results))
original.traverse.__code__=base
out=dict(result='PASS_EXACT_MULTI_FIXTURE_PORTAL_POINT_CACHE',fixtures=len(rows),samples=384,rows=rows,scope='Four captured scene pairs, independent unchanged source reference, alternating complete six-sample preparation; excludes construction. Not chronological multi-pair history, live cadence, independent original fidelity or scanout proof.')
Path('outputs/nfsug-native-renderer/camera-research/portal-point-cache-multifixture-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
for row in rows:print(row['identities'],row['median_ms'])
