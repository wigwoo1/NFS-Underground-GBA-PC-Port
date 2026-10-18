"""Verify exact retained publication ownership and availability margins."""
import json,sys,statistics
from pathlib import Path
def analyze(raw,m):
 assert m['dropped']==0 and m['rows']
 requests={}
 for q in raw['world_preparation_stage_samples']:
  key=tuple([q['generation'],q['older'],q['newer']]);assert key not in requests;requests[key]=q
 records=[];missing=0
 for row in m['rows']:
  assert row['ready_ns']<=row['returned_ns'] and row['requested_ns']<=row['returned_ns']
  assert row['available_before_request_ns']==row['requested_ns']-row['ready_ns']
  assert 0<row['alpha']<1 and row['kind'] in ('sample','first_take')
  q=requests.get(tuple(row['identity']))
  if q is None:missing+=1;continue
  matches=[p for p in q['parent_sample_rows'] if p['publication_begin_ns']<=row['ready_ns']<=p['published_ns']]
  assert len(matches)==1,(row,matches)
  records.append(dict(row,sample_index=matches[0]['index']))
 assert records and missing==0
 groups={}
 for kind in ('sample','first_take'):
  g=[x for x in records if x['kind']==kind];assert g
  groups[kind]=dict(count=len(g),late=sum(x['available_before_request_ns']<0 for x in g),minimum_margin_ms=min(x['available_before_request_ns'] for x in g)/1e6,median_margin_ms=statistics.median(x['available_before_request_ns'] for x in g)/1e6,max_call_ms=max(x['returned_ns']-x['requested_ns'] for x in g)/1e6)
 return dict(result='PASS_EXACT_SAMPLE_READINESS_OWNERSHIP',groups=groups,latest=sorted(records,key=lambda x:x['available_before_request_ns'])[:20],scope='Actual call request versus publication inside owned pair lock, exact completed source-pair/publication match. API request time differs from intended presentation deadline; no sustained60 or exclusive stall-cause proof.')
if __name__=='__main__':
 raw=json.loads(Path(sys.argv[1]).read_text());m=json.loads(Path(sys.argv[2]).read_text());out=analyze(raw,m)
 from copy import deepcopy
 bad=deepcopy(m);bad['rows'][0]['ready_ns']=bad['rows'][0]['returned_ns']+1
 try:analyze(raw,bad)
 except AssertionError:pass
 else:raise AssertionError('Impossible availability accepted')
 out['negative_control_rejected']=True;Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out['result'],out['groups'])
