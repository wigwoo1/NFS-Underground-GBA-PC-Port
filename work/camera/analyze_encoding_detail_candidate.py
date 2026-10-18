import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[];checks=0
for request in ledger['records']:
 b=request['child_boundaries'];a=b['sampled_ns'];z=b['encoded_ns'];intervals=[]
 assert request['encode_sample_encoding']=='alpha_start_end_cycles_framebytes_tailindex_v1' and not request['encode_samples_truncated']
 assert len(request['encode_samples'])==request['encode_sample_count']
 total=0;last=a
 for alpha,start,end,cycles,framebytes,index in request['encode_samples']:
  assert last<=start<=end<=z and cycles>=0 and framebytes>=40
  total+=end-start;last=end;intervals.append((start,end));checks+=1
 side=request['source_sidecar_trace'];cleanup=request['encoding_cleanup']
 side_ns=0
 if side:
  assert last<=side['begin_ns']<=side['end_ns']<=z
  side_ns=side['end_ns']-side['begin_ns'];intervals.append((side['begin_ns'],side['end_ns']));last=side['end_ns']
 close_ns=replacement_ns=0
 if cleanup:
  ca,cb,ra,rb=[cleanup[k] for k in ['close_begin_ns','close_end_ns','replacement_begin_ns','replacement_end_ns']]
  assert last<=ca<=cb<=ra<=rb<=z
  close_ns=cb-ca;replacement_ns=rb-ra;intervals.extend([(ca,cb),(ra,rb)])
 measured=total+side_ns+close_ns+replacement_ns;assert measured<=z-a
 rows.append(dict(older=request['older'],newer=request['newer'],encode_ms=(z-a)/1e6,samples_ms=total/1e6,sidecar_ms=side_ns/1e6,close_ms=close_ns/1e6,replacement_ms=replacement_ns/1e6,remainder_ms=(z-a-measured)/1e6))
out=dict(result='PASS_COMPLETE_SLOW_ENCODING_DETAIL',requests=len(rows),sample_checks=checks,rows=sorted(rows,key=lambda x:x['encode_ms'],reverse=True),scope='Complete bounded slow-request ledger, exact nonoverlapping phase containment. Elapsed may include scheduling; not exclusive CPU or visible60 proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(requests=len(rows),sample_checks=checks,largest=out['rows'][:3]),indent=2))
