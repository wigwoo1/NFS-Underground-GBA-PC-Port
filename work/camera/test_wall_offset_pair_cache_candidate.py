import json,struct
from dataclasses import replace
from pathlib import Path
from owned_closed_graph import ClosedGraph
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_sampled_graph_wall_visibility import selected_graph_walls as baseline
import owned_sampled_graph_wall_visibility_offset_cache_candidate as candidate
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);checks=0;cache_hits=0
for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(fa['graph']).read_bytes()).graph;b=ClosedGraph.decode(Path(fb['graph']).read_bytes()).graph
 motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());base=PortalMotionPair(a,b,table,motion);fast=PortalMotionPair(a,b,table,motion)
 for alpha in (0,.001,.25,.5,.75,.999,1):
  expected=baseline(base,alpha)
  assert expected==candidate.selected_graph_walls_plain(fast,alpha)==candidate.selected_graph_walls_traced(fast,alpha);checks+=1
  assert [x['name'] for x in fast._last_wall_selection_stages]==['metadata_and_camera','candidate_generation','candidate_edges','visibility_batch','selection_and_order']
  if alpha not in (0,1):assert fast._verified_wall_offset_owners==(a,b)
 # Replace packet owner with valid immutable bytes differing in offset data.
 changed=bytearray(b.offsets);changed[0]^=1;bad=replace(b,offsets=bytes(changed));fast.newer=bad
 try:candidate.verified_offset_pair(fast)
 except ValueError:pass
 else:raise AssertionError('Changed packet owner offset mismatch accepted')
 fast.newer=b;candidate.verified_offset_pair(fast)
 # Owner cache must skip metadata comparison entirely on next call.
 original=candidate.wall_metadata
 def forbidden(*args):raise AssertionError('Repeated immutable offset metadata comparison')
 candidate.wall_metadata=forbidden
 try:candidate.verified_offset_pair(fast);cache_hits+=1
 finally:candidate.wall_metadata=original
out=dict(result='PASS_IMMUTABLE_WALL_OFFSET_PAIR_PARITY',samples=checks,verified_cache_hits=cache_hits,replaced_owner_mismatch_rejected=cache_hits,scope='Real15graphpairs/105samples, plain and traced outputs exactly baseline; all five diagnostic stages retained. No comparative speedup claim.')
Path('work/camera/prototype-runs/wall-offset-pair-cache-parity-20261010.json').write_text(json.dumps(out,indent=2));print(out)
