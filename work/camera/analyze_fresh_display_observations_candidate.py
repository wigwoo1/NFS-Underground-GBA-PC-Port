import json,sys,collections
from pathlib import Path
r,l,o=[json.loads(Path(x).read_text()) for x in sys.argv[1:4]];assert not l['dropped'] and not o['dropped']
s=[x for x in r['presentation_samples'] if x.get('presentation_backend')=='dxgi_flip_sequential'];assert len(s)==len(l['rows'])
sub={};identities=set()
for x,t in zip(s,l['rows']):
 assert t[4]==t[6] and t[5]==0
 sub[t[6]]=dict(epoch=x['epoch'],generation=x['generation'],index=x['display_index']);identities.add(t[13])
observed={};by_point=collections.defaultdict(set);errors=collections.Counter();ages=[]
for t in o['rows']:
 assert len(t)==16 and t[3]<=3 and t[4]<=t[5] and t[6]>0 and t[15] in identities
 assert t[8]==0 and t[7]==t[9] and 0<=t[9]<=len(sub)
 errors[hex(t[10])]+=1
 if t[10] or not t[11] or not t[14]:continue
 assert t[11] in sub and t[11]<=t[9]
 by_point[t[3]].add(t[11]);ages.append(t[9]-t[11])
 if t[11] in observed:assert observed[t[11]]['refresh']==t[12]
 else:observed[t[11]]=dict(present_id=t[11],refresh=t[12],sync_refresh=t[13],sync_qpc=t[14],frequency=t[6],render=sub[t[11]])
out=dict(result='OBSERVATION_COVERAGE_ONLY_DISPLAY_UNVERIFIED',submissions=len(sub),observations=len(o['rows']),observed_ids=len(observed),unobserved_ids=sorted(set(sub)-set(observed)),unique_ids_by_point={k:len(v) for k,v in by_point.items()},statistics_hresult_counts=dict(errors),max_observation_age_submissions=max(ages) if ages else None,observed=list(observed.values()),scope='Fresh owner-thread statistics at exact frame boundaries; observed ID joins only. Missing IDs are not classified dropped, sparse coverage cannot certify60fps.')
Path(sys.argv[4]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['unobserved_ids','observed']})
