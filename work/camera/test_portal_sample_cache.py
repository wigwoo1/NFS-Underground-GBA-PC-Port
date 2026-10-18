import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
import owned_motion_visibility as visibility
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());a,b=r['wall_diagnostic_frames'][:2];ga=ClosedGraph.decode(Path(a['graph']).read_bytes());gb=ClosedGraph.decode(Path(b['graph']).read_bytes());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);motion=PreparedMotionPair(Path(a['regenerated']).read_bytes(),Path(b['regenerated']).read_bytes());pair=visibility.PortalMotionPair(ga.graph,gb.graph,table,motion);original=visibility.sampled_regions;calls=[]
def tracked(*args,**kwargs):calls.append(args[4]);return original(*args,**kwargs)
visibility.sampled_regions=tracked
try:
 first=pair.sample(.5);assert pair.sample(.5) is first and pair.sample(.5) is first and len(calls)==1
 pair.sample(.25);assert pair.sample(.5)==first and len(calls)==2
 for alpha in (.1,.2,.3,.4,.6,.7,.8,.9):pair.sample(alpha)
 assert len(pair._samples)==8 and .5 not in pair._samples
 before=len(calls);assert pair.sample(.5)==first and len(calls)==before+1
 for invalid in (float('nan'),-1,2):
  try:pair.sample(invalid)
  except ValueError:pass
  else:raise AssertionError('Invalid cached alpha accepted')
 assert isinstance(first,tuple) and all(isinstance(x,tuple) for x in first)
finally:visibility.sampled_regions=original
Path('work/camera/portal-sample-cache-tests.json').write_text(json.dumps(dict(result='PASS_BOUNDED_PORTAL_SAMPLE_CACHE',same_alpha_traversals=1,changed_alpha_traversals=2,eviction_verified=True,capacity=8,invalid_samples_rejected=3),indent=2));print('PASS_BOUNDED_PORTAL_SAMPLE_CACHE')
