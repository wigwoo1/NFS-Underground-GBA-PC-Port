import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['producer_retention']['long_scene_preparations'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for scene in ledger['records']:
 for call in scene['frame_read_boundaries']:
  s=call['reader_stages'];p=call['native'];assert len(s)==12 and s[1]==scene['refresh'] and s[9]==p[10]==p[11] and s[10:]==[1,160] and s[2]==p[12]
  assert sum(s[3:8])==s[8] and 0<=s[8]<=p[7]-p[6]
  values={k:s[i]*1000/s[2] for i,k in enumerate(('geometry_ms','hud_ms','background_ms','text_ms','other_ms','whole_ms'),3)}
  rows.append(dict(refresh=s[1],**values))
assert rows
out=dict(result='PASS_NATIVE_READER_STAGE_PARTITION',count=len(rows),median_ms={k:statistics.median(x[k] for x in rows) for k in rows[0] if k!='refresh'},max_ms={k:max(x[k] for x in rows) for k in rows[0] if k!='refresh'},records=rows,scope='Complete longscene subset. Perrow QPC instrumentation adds overhead and elapsed includes scheduling; no exclusive CPU attribution or cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='records'}))
