"""Compare recorded original span inputs with reconstructed wall columns; no repair."""
from pathlib import Path
import json,struct
base=Path('C:/NFSUG-Workspace/NFSUG-wall-span-trace-fixtures');proof=json.loads((base/'original-wall-address-report.json').read_text());targets=sorted({p['original_span_index'] for p in proof['points']});raw=(base/'original-wall-spans.nws').read_bytes();spans=[];at=0
while at<len(raw):h=struct.unpack_from('<45I',raw,at);spans.append(h);at+=h[2]
columns=[]
with (base/'original-wall-events.nwj').open('rb') as f:
 while header:=f.read(96):
  h=struct.unpack('<12Q',header);assert h[0]==0x314a574e and h[6]==2 and h[11]==20;commands=f.read(h[7]*80);assert len(commands)==h[7]*80;f.seek(h[10],1)
  if h[5]>=12098:
   for i in range(h[7]):columns.append((h[4],h[5],i,struct.unpack_from('<20I',commands,i*80)))
results=[]
for index in targets:
 h=spans[index];s=h[28:45];r=h[12:28];matches=[]
 for event,frame,column,c in columns:
  if h[6]<=frame<=h[7] and c[9]==s[9] and c[17]==r[1]:matches.append(dict(event=event,frame=frame,column=column,top=c[1],count=c[19],vertical=c[18],horizontal=c[13],step=c[11],differing_state_words=[i for i in range(17) if c[i]!=s[i]]))
 results.append(dict(span=index,frame=h[7],serial=h[5],begin=h[6],destination=r[1],texture=s[9],top=s[1],count=r[3],vertical=r[2],horizontal=s[13],step=s[11],reconstructed=matches))
report=dict(result='ORIGINAL_VS_RECONSTRUCTED_WALL_COLUMNS',target_original_spans=len(targets),no_exact_context_columns=sum(not r['reconstructed'] for r in results),columns=results)
assert report['target_original_spans']==19 and report['no_exact_context_columns']==15
(base/'wall-column-comparison.json').write_text(json.dumps(report,indent=2));print('CONFIRMED:19 original spans,15 missing reconstructed contexts; no renderer mutation')
