import json,sys,statistics
from pathlib import Path
source,blit,prep,out=map(Path,sys.argv[1:5]);s=json.loads(source.read_text());b=json.loads(blit.read_text());p=json.loads(prep.read_text())['rows']
for value in (s,b):assert value['stats']==[len(value['rows'])*2,len(value['rows'])*2,0]
sm={tuple(r[:3]):r for r in s['rows']};bm={tuple(r[:3]):r for r in b['rows']};assert len(sm)==len(s['rows']) and len(bm)==len(b['rows'])
rows=[]
for r in p:
 k=tuple(r[:3]);a=sm[k];c=bm[k]
 assert a[6]==c[6]==0 and a[7] in (1,3) and c[7] in (1,3)
 for q in (a,c):
  if q[7]==1:assert q[4]>=q[3]
 rows.append(dict(identity=k,source_gpu_ms=(a[4]-a[3])/1e6 if a[7]==1 else None,blit_gpu_ms=(c[4]-c[3])/1e6 if c[7]==1 else None,lock_ms=(r[5]-r[4])/1e6,unlock_ms=(r[7]-r[6])/1e6))
assert len(bm)==len(rows)
def metrics(field):
 v=[r[field] for r in rows if r[field] is not None];return dict(resolved=len(v),median_ms=statistics.median(v),max_ms=max(v))
r=dict(result='PASS_EXACT_SOURCE_BLIT_TRANSFER_JOIN',transfers=len(rows),source_queries=len(sm),blit_queries=len(bm),source_stats=s['stats'],blit_stats=b['stats'],source_gpu=metrics('source_gpu_ms'),blit_gpu=metrics('blit_gpu_ms'),slow_transfers=sum(max(r['lock_ms'],r['unlock_ms'])>20 for r in rows),top_stalls=sorted(rows,key=lambda r:max(r['lock_ms'],r['unlock_ms']),reverse=True)[:10],scope='GPU timestamp brackets include scheduling. Exact identities, no cross-clock subtraction. No physical cadence or exclusive driver causality claim.')
out.write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
