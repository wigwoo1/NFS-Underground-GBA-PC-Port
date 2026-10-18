"""Verify source-boundary opponent pose before any visible matrix build."""
import sys,json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
from owned_model_builder_inputs import OwnedModelBuilders,BuilderInputs
from owned_external_model_projection import external_model_matrix
from owned_scene_bundle import chunks
from owned_motion_pairs import records
report=json.loads(Path(sys.argv[1]).read_text());evidence=[]
for capture in report['model_scene_captures']:
 closed=ClosedGraph.decode(Path(capture['graph']).read_bytes());sources=OwnedModelSources.decode(Path(capture['current-sources']).read_bytes(),closed);builders=OwnedModelBuilders(Path(capture['builders']).read_bytes())
 base=struct.unpack_from('<I',closed.graph.context,60)[0];address=base+164;source=sources.sources[address];enabled,external=sources.external[address]
 assert enabled and struct.unpack_from('<h',source,54)[0]==7 and struct.unpack_from('<H',source,10)[0]&32
 chain=[]
 for h,raw in chunks(closed.objects,'graph_objects'):
  for i in range(h[5]):
   if struct.unpack_from('<I',raw,128+i*168)[0]==1:chain.append((h[3],raw[132+i*168:296+i*168]))
 assert len(chain)==1 and chain[0][1]==source
 candidate=BuilderInputs(closed.graph.refresh,0,address,0,source,closed.graph.context[256:304],bytes(48),enabled,external)
 pose=external_model_matrix(candidate)
 prior=[b for (a,_),values in builders.records.items() if a==address for b in values if b.refresh<=closed.graph.refresh]
 exact_draws=[i for i,row in enumerate(records(Path(capture['frame']).read_bytes())['records']) if row['kind']==3 and bytes(row['blocks'][2])==pose]
 evidence.append(dict(refresh=closed.refresh,source_refresh=closed.graph.refresh,parent=chain[0][0],slot=source[136],prior_builders=len(prior),candidate_pose=struct.unpack('<12i',pose),exact_draws=exact_draws))
assert evidence and evidence[0]['prior_builders']==0,'Capture did not include pre-builder source'
assert len({tuple(x['candidate_pose']) for x in evidence})==len(evidence),'Held candidate pose'
Path(sys.argv[1]).with_suffix('.prebuilder-opponent.json').write_text(json.dumps(evidence,indent=2))
print('PASS original source/chain/external closure before first builder and',len(evidence),'distinct boundary poses')
print(evidence)
