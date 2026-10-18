"""Separate actual native reads from allocation and Python return boundaries."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['producer_retention']['long_scene_preparations'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for scene in ledger['records']:
 for call in scene['frame_read_boundaries']:
  p=call['native'];assert len(p)==15 and all(a<=b for a,b in zip(p[:9],p[1:10])) and p[10]==p[11] and p[12]>0
  ns=lambda t:t*1000000000//p[12]
  assert call['started_ns']<=ns(p[0])<=ns(p[9])<=call['completed_ns']
  ms=lambda a,b:(p[b]-p[a])*1000/p[12]
  rows.append(dict(refresh=scene['refresh'],query_ms=ms(1,2),query_return_ms=ms(2,3),allocation_ms=ms(4,5),read_ms=ms(6,7),read_return_ms=ms(7,8),header_ms=ms(8,9),whole_extension_ms=ms(0,9),query_cycles=p[13],read_cycles=p[14],bytes=p[10]))
assert rows
out=dict(result='PASS_LONG_CAPTURE_NATIVE_BOUNDARY_PARTITION',long_scene_count=ledger['total'],capture_rows=len(rows),medians={k:statistics.median(x[k] for x in rows) for k in rows[0] if k not in ('refresh','bytes')},maximum={k:max(x[k] for x in rows) for k in ('query_ms','query_return_ms','allocation_ms','read_ms','read_return_ms')},records=rows,scope='Complete longscene capture ledger only, not all captures. Native elapsed can include scheduling; return spans include GIL reacquisition, no exclusive causality or cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='records'}))
