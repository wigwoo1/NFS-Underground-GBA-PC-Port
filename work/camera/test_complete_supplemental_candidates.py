import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_closed_supplemental_calls import calls
from owned_supplemental_eligibility import supplemental_eligibility
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[]
for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes())
 sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
 motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());portal=PortalMotionPair(a.graph,b.graph,table,motion)
 pair=CompleteSupplementalCandidates(a,b,sa,sb,portal,rom);samples=[]
 for alpha in (0,.001,.25,.5,.75,.999,1):
  candidates=pair.sample(alpha)
  if alpha in (0,1):
   expected=calls(a,sa) if alpha==0 else calls(b,sb)
   assert [(c.parent,c.object,c.descriptor) for c in candidates]==[(c.parent_descriptor,c.object_index,c.descriptor) for c in expected]
   assert {(c.parent,c.object,c.descriptor,c.bounds,c.depth) for c in candidates}=={(c.parent_descriptor,c.object_index,c.descriptor,tuple(float(x) for x in c.parent_region[1:5]),float(__import__('owned_object_filter').depth_distance(c.source,(a if alpha==0 else b).graph.context[256:304])[0])) for c in expected}
  assert all(c.eligibility=='project' for c in candidates)
  assert all(c.depth>0 and len(c.wall_edges)==4 and c.bounds[0]<=c.bounds[1] and c.bounds[2]<=c.bounds[3] for c in candidates)
  samples.append(dict(alpha=alpha,candidates=len(candidates),pending_callbacks=sum(c.eligibility=='callback' for c in candidates),descriptors=[c.descriptor for c in candidates]))
 for endpoint,near in ((0,1e-8),(1,1-1e-8)):
  exact=pair.sample(endpoint);adjacent=pair.sample(near)
  assert [(c.parent,c.object,c.descriptor) for c in exact]==[(c.parent,c.object,c.descriptor) for c in adjacent]
  assert all(abs(x.distance-y.distance)<1e-3 for x,y in zip(exact,adjacent))
 checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
bad=bytearray(pair.dependencies[0][0].source);struct.pack_into('<H',bad,78,11)
try:supplemental_eligibility(bytes(bad))
except ValueError:pass
else:raise AssertionError('Unsupported callback accepted')
out=dict(result='PASS_COMPLETE_SUPPLEMENTAL_CANDIDATES',intervals=len(checks),checks=checks,scope='Complete raw asset candidate enumeration and sampled parent/depth. Selector12 eligibility resolved; 30 endpoint ordered invocation lists and identity/bounds/depth sets match original captures; near-endpoint distance continuity verified. Complete cross-kind/deferred ordering, callback effects and intermediate surface visibility remain unverified.')
Path('work/camera/complete-supplemental-candidate-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks),checks[0]['samples'][0])





