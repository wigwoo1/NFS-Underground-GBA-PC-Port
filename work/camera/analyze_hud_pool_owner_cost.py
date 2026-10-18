import json, math, re, sys
from pathlib import Path
path=Path(sys.argv[1]); rows=[]; pending=None
fields=('geometry_validation','road_display_validation','hud_pool_construction','allocation','copy')
for line in path.read_text().splitlines():
    if line.startswith('owned_hud_pool '):
        pending={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
        assert pending['epoch']>0 and 0<pending['stored_bytes']<=pending['full_bytes']+688
    if line.startswith('motion_owner_profile '):
        assert pending is not None, 'Profile without pool'
        values=dict(re.findall(r'(\w+)=([0-9.]+)',line))
        assert all(k in values for k in fields)
        row={k:float(values[k]) for k in fields}
        assert all(math.isfinite(v) and v>=0 for v in row.values())
        row.update(pending); row['total_ms']=sum(row[k] for k in fields); rows.append(row);pending=None
assert rows, 'No profiled pooled owners'
def stats(values):
    v=sorted(values);return dict(count=len(v),mean=sum(v)/len(v),median=v[len(v)//2],p95=v[math.ceil(.95*len(v))-1],maximum=v[-1])
result={'source':str(path.resolve()),'scope':'Successful owner construction wall times; excludes failed captures and later validation; no causal or 60fps proof',
        'stages_ms':{k:stats([r[k] for r in rows]) for k in (*fields,'total_ms')},
        'storage_groups':{label:{'count':len(group),'pool_ms':stats([r['hud_pool_construction'] for r in group])} for label,group in
            ((label,[r for r in rows if lo<=r['stored_bytes']<hi]) for label,lo,hi in [('under_256KiB',0,262144),('256KiB_to_1MiB',262144,1048576),('over_1MiB',1048576,1<<60)]) if group},
        'slowest_owners':sorted(rows,key=lambda r:r['total_ms'],reverse=True)[:8]}
print(json.dumps(result,indent=2))
