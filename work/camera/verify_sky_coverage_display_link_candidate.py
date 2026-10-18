"""Check captured native pixels against bounded reported DXGI ownership."""
import json,sys
from pathlib import Path
src=Path(sys.argv[1]);r=json.loads(src.read_text());reported=[];missing=[]
assert not r['missed'] and r['pending']==0 and len(r['rows'])==48
for row in r['rows']:
 row=dict(row,identity=[row['epoch'],row['generation'],row['index']])
 d=row.get('display_report')
 if d is None:missing.append(row['identity']);continue
 assert d['native_identity']==row['identity'] and d['statistics'][0:2]==[0,0] and d['statistics'][3]>0
 assert len(d['statistics'])==9 and d['statistics'][8]>0
 assert d['observed_at_native_identity'][:2]==row['identity'][:2] and d['observed_at_native_identity'][2]>=row['identity'][2]
 assert row['native_result']==1 and row['commit'][4]==row['identity'][2] and row['commit'][:2]==row['identity'][:2]
 reported.append(row['identity'])
out=dict(result='BOUNDED_SKY_COVERAGE_TO_DXGI_REPORT_LINK',source=str(src.resolve()),captures=len(r['rows']),reported_captures=len(reported),unreported_captures=len(missing),unique_reported_frames=len(set(map(tuple,reported))),missing_native_identities=sorted(set(map(tuple,missing))),scope='DXGIreportedpresentcount mapped to capturednativeidentity byownerobserver. Missingreports notexcusedasdisplayed; no physicalpixel/4Kscanoutcertification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
