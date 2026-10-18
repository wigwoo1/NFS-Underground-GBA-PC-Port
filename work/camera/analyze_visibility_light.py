import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for tid,v in r['records']:
 assert len(v)==12 and v[1]<=v[2]<=v[4]<=v[6]<=v[8]<=v[10]
 parts=[dict(name=n,ms=(v[4+i*2]-v[2+i*2])/1e6,cycles=v[5+i*2]-v[3+i*2]) for i,n in enumerate(('domain_validation','input_packing','native_call','output_conversion'))]
 rows.append(dict(thread_id=tid,count=v[0],started_ns=v[1],wall_ms=(v[10]-v[1])/1e6,diagnostic_setup_ms=(v[2]-v[1])/1e6,phases=parts))
out=dict(result='PASS_BOUNDED_LIGHT_TRACE',completed=r['completed'],slow_count=len(rows),dropped=r['dropped'],largest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:5],scope=r['scope']);Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
