"""Actual native presentation QPC/cycle stages, no scanout proof."""
import json,sys,statistics,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());v=collections.defaultdict(list);tails=[]
for row in r['presentation_samples']:
 p=row.get('presentation')
 if not p:continue
 x=p['native_c_profile'];q=x[:4];c=x[4:8];f=x[8]
 assert f>0 and all(b>=a for a,b in zip(q,q[1:])) and all(b>=a for a,b in zip(c,c[1:]))
 wall=[(q[i+1]-q[i])*1000/f for i in range(3)];cycles=[c[i+1]-c[i] for i in range(3)]
 for i,name in enumerate(['get_buffer','copy_and_release','present']):v[name].append(wall[i]);v[name+'_cycles'].append(cycles[i])
 tails.append(dict(index=row['display_index'],wall_ms=wall,thread_cycles=cycles,status=p['status']))
stats={}
for name,a in v.items():
 a.sort();stats[name]=dict(count=len(a),median=statistics.median(a),p95=a[int((len(a)-1)*.95)],max=max(a),units='cycles' if name.endswith('_cycles') else 'ms')
result=dict(result='MEASURED_NATIVE_PRESENT_STAGES',stages=stats,largest_total=sorted(tails,key=lambda x:sum(x['wall_ms']),reverse=True)[:8],scope='Native QPC wall and thread cycle deltas, GetBuffer/CopyResource+release/Present. Cycle counts cannot convert to execution time without frequency and wall includes descheduling/driver wait. All occlusion retained; no visible scanout or60fps proof')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
