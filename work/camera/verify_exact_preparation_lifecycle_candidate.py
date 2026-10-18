"""Actual exact preparation shutdown audit, separate from native handoff cleanup."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
s=r['frame_preparation_shutdown'];assert s['joined'] is True and s['pending']==0
assert s['owner_alive_after_preparation_join'] is True and s['owner_released_after_renderer_close'] is True
assert 0<=s['peak']<=s['capacity']==2 and s['hits']>=0 and s['misses']>=0
assert s['hits']+s['misses']>=r['owned_scene_submissions']
out=dict(result='PASS_EXACT_PREPARATION_OWNER_LIFECYCLE',shutdown=s,scope='Preparation thread joined and private ready buffers cleared while native owner alive, then renderer owner released. Ordinary shutdown only, no forced race or60fps evidence.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
