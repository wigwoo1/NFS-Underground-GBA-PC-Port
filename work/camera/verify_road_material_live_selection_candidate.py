import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['world_preparation_stage_samples']
assert r['result']=='SMOKE_COMPLETE' and rows
previous=None
for row in rows:
 stats=row['terminal'][5]['road_material_resolution_stats']
 assert stats and stats['calls']>0 and stats['candidates']>0
 if previous is not None:assert stats['calls']>=previous['calls'] and stats['candidates']>=previous['candidates']
 previous=stats
out=dict(result='PASS_CHILD_ROAD_MATERIAL_RESOLUTION_SELECTION',requests=len(rows),final_stats=previous,scope='Every retained complete child request reports cumulative candidate execution; complete transfer accounting audited separately.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
