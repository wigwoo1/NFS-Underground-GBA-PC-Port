import sys,json,time,statistics
from pathlib import Path
sys.argv=[__file__,'work/camera/prototype-runs/child-scene-1791637661169682300'];ns={};exec(Path('work/camera/test_current_wall_record_scopes.py').read_text().split('from owned_progressive_source_samples_candidate')[0],ns)
from owned_closed_scene_memory import ClosedSceneMemory as Original
import owned_geometry_range_reuse_candidate as candidate
candidate.clear();timings={False:[],True:[]};checks=0
try:
 for i in range(40):
  for selected in ((False,True) if i%2==0 else (True,False)):
   for scene in ns['scenes']:
    start=time.perf_counter_ns();memory=(candidate.ClosedSceneMemory if selected else Original)(scene.graph,ns['rom']);timings[selected].append(time.perf_counter_ns()-start)
    reference=Original(scene.graph,ns['rom']);assert (memory._ranges,memory._starts,memory.owned_byte_count)==(reference._ranges,reference._starts,reference.owned_byte_count)
    for address,data in memory._ranges:assert memory.read(address,len(data))==reference.read(address,len(data))
    checks+=1
finally:ns['history'].close()
assert candidate.stats['hits']>0
out=dict(result='PASS_EXACT_GEOMETRY_RANGE_COMPONENT',constructors=checks,stats=dict(candidate.stats),baseline_median_ms=statistics.median(timings[False])/1e6,candidate_median_ms=statistics.median(timings[True])/1e6,scope='Two saved endpoints,40alternating rounds, exact complete mergedranges/starts/ownedbytes/allcontainedreads. Component notlive or fullscene qualification.')
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/geometry-range-reuse-20261010');p.mkdir(exist_ok=True);(p/'component.json').write_text(json.dumps(out,indent=2));print(out)
