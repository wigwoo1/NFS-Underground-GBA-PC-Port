import json,statistics
from pathlib import Path
base=Path('work/camera/prototype-runs');names=['owned-native-1791607169505750800.json','owned-native-1791607071513957000.json'];rows=[];index=[]
for name in names:
 r=json.loads((base/name).read_text());l=r['boundary_retention']['complete_dequeues'];assert l['dropped']==0;d={};occurrences={}
 for x in l['records']:
  refresh=x['refresh'];ordinal=occurrences.get(refresh,0);occurrences[refresh]=ordinal+1;d[(refresh,ordinal)]=x
 assert len(d)==len(l['records']);index.append(d)
 assert r['owned_scene_submissions']==406 and r['presentations']==1764 and r['smoke_scripted_inputs']
common=sorted(set(index[0])&set(index[1]));matching=[k for k in common if index[0][k]['frame_bytes']==index[1][k]['frame_bytes']];assert len(matching)>390
for k in matching:rows.append(dict(refresh=k[0],occurrence=k[1],bytes=index[0][k]['frame_bytes'],baseline_ms=(index[0][k]['copied_ns']-index[0][k]['snapshot_ready_ns'])/1e6,candidate_ms=(index[1][k]['copied_ns']-index[1][k]['snapshot_ready_ns'])/1e6))
out=dict(result='FRAME_MATCH_BINDING_COMPARISON_UNPROMOTED',matched_refresh_and_size=len(rows),baseline_mean_ms=statistics.mean(x['baseline_ms'] for x in rows),candidate_mean_ms=statistics.mean(x['candidate_ms'] for x in rows),rows=rows,scope='Single sequential30ssteering/pause pair matched byrefresh andbytesize; bytecontentcrossrun equality notclaimed. Candidate has65mschildpreparationstall whilebaseline max22.6ms; notrepeatablecausalwhole-game performancebenefit.')
(base/'frame-match-binding-comparison-20261010.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
