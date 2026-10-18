"""Whole acknowledged-request aggregate stages, no retained quantiles."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['shutdown_evidence']['preparation_service_shutdown'];assert s['child_alive'] is False and s['child_exitcode']==0 and s['forced_termination'] is False and s['request_mapping_closed'] is True
count=s['request_acknowledged'];assert count>0;stats={}
for name,row in s['request_stage_totals'].items():
 assert row['count']==count and 0<=row['max_ns']<=row['total_ns']
 stats[name]=dict(count=count,mean_ms=row['total_ns']/count/1e6,max_ms=row['max_ns']/1e6,total_ms=row['total_ns']/1e6)
out=dict(result='PASS_WHOLE_SHARED_REQUEST_STAGE_AND_OWNER_AUDIT',stats=stats,scope='Whole successful acknowledged requests, no quantiles. Ack wait includes child copy/validation and scheduling. Warm startup and failed requests excluded. No exclusive CPU or visible60 evidence.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
