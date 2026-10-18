import sys,json,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());groups={k:[] for k in ('get_buffer','copy_and_release','dxgi_present','native_total','outer_callback','outside_native')};records=[]
for row in r['presentation_samples']:
 if row['native_result']!=1:continue
 p=row['presentation']['native_present_profile'];assert len(p)==5 and p[4]>0 and p[:4]==sorted(p[:4])
 timing=row['callback_timing'];outer=(timing['present_end_ns']-timing['present_begin_ns'])/1e6
 parts=[(p[i+1]-p[i])*1000/p[4] for i in range(3)];total=sum(parts)
 assert outer>=0 and outer-total>=-.1,(outer,total)
 values=parts+[total,outer,max(0,outer-total)]
 record=dict(index=row['display_index'],epoch=row['epoch'],generation=row['generation'],**dict(zip(groups,values)));records.append(record)
 for name,value in zip(groups,values):groups[name].append(value)
assert records
result=dict(result='PASS_NATIVE_PRESENT_SUBSTAGES',samples=len(records),stages={},slowest=sorted(records,key=lambda x:x['outer_callback'],reverse=True)[:20],scope='Native QPC wall times nested inside callback; outside_native includes queue dispatch/future completion, message pumping, Python/ctypes and scheduling. DXGI time includes blocking/scheduling, not pure GPU cost. Physical scanout unverified.')
for name,values in groups.items():
 v=sorted(values);result['stages'][name]=dict(median_ms=statistics.median(v),p95_ms=v[int(.95*(len(v)-1))],max_ms=v[-1])
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='slowest'},indent=2))
