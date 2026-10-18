from pathlib import Path
import re,json,statistics,sys
p=Path(sys.argv[1]);rows=[dict(re.findall(r'(\w+)=([-\d.]+)',line)) for line in Path(str(p)+'-host.log').read_text().splitlines() if line.startswith('motion_owner_profile ')];assert rows
out=dict(result='OWNED_CONSTRUCTOR_COSTS',prefix=str(p),constructors=len(rows),stages={})
for k in ('geometry_validation','road_display_validation','allocation','copy'):
 v=sorted(float(r[k]) for r in rows);assert min(v)>=0;out['stages'][k]=dict(sum_ms=sum(v),median_ms=statistics.median(v),p95_ms=v[int((len(v)-1)*.95)],max_ms=max(v))
out['allocated_owner_bytes']=sum(int(r['bytes']) for r in rows);fields=('header_bytes','camera_bytes','older_bytes','newer_bytes','packet_bytes','road_bytes','hud_bytes','text_bytes')
if all(all(k in r for k in fields) for r in rows):
 assert all(sum(int(r[k]) for k in fields)==int(r['bytes']) for r in rows)
 out['allocation_sections']={k:sum(int(r[k]) for r in rows) for k in fields}
 out['copied_payload_bytes']=sum(out['allocation_sections'][k] for k in fields if k!='header_bytes')
out['scope']='Successful constructor wall stages; broad complete_clone capture label additionally includes occurrence-negative and provenance work.'
Path(str(p)+'-constructor-analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
