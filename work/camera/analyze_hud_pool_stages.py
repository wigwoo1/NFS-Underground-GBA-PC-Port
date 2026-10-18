import json,math,re,statistics,sys
from pathlib import Path
rows=[]
for line in Path(sys.argv[1]).read_text().splitlines():
 if not line.startswith('hud_pool_cost '):continue
 d=dict(re.findall(r'(\w+)=([0-9.]+)',line));r={k:(float(v) if k.endswith('_ms') else int(v)) for k,v in d.items()}
 assert r['epoch']>0 and all(1<=r[k]<=160 for k in ('obj','palette','oam')) and r['filter'] in (0,1)
 assert r['bytes']==21160+32*r.get('sha256',0)+r['obj']*32768+(r['palette']+r['oam'])*1024
 assert all(math.isfinite(r[k]) and r[k]>=0 for k in ('dedup_ms','storage_ms','checksum_ms'))
 rows.append(r)
assert rows
groups={}
for mode in (0,1):
 group=[r for r in rows if r['filter']==mode]
 if group:groups[str(mode)]={k:{'count':len(group),'mean':statistics.mean(r[k] for r in group),'max':max(r[k] for r in group)} for k in ('dedup_ms','storage_ms','checksum_ms')}
print(json.dumps({'records':len(rows),'groups_ms':groups,'scope':'Profiled constructor stage wall times; exact native extent/count checked; includes OS scheduling and measurement overhead, excludes log output from stage timings'},indent=2))

