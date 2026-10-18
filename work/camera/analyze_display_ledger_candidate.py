import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=json.loads(Path(sys.argv[2]).read_text());a=[s for s in r['presentation_samples'] if s.get('presentation_backend')=='dxgi_flip_sequential'];p=ledger['rows'];assert len(a)==len(p)>0 and ledger['dropped']==0
positive=[];errors={};identities=set()
for i,(s,t) in enumerate(zip(a,p)):
 assert len(t)==14 and t[0]==s['epoch'] and t[1]<=t[2] and t[3]>0
 begin=t[1]*1000000000//t[3];end=t[2]*1000000000//t[3]
 assert s['native_commit_stage_ns'][3]-2<=begin<=end<=s['native_commit_stage_ns'][4]+2
 assert t[5]==0 and t[4]==t[6]==i+1;identities.add(t[13]);errors[hex(t[7])]=errors.get(hex(t[7]),0)+1
 if t[7]==0 and t[8]>0 and t[11]>0:positive.append(t)
out=dict(result='PASS_SUBMISSION_IDENTITY_DISPLAY_UNPROVEN' if not positive else 'POSITIVE_DISPLAY_STATS_REQUIRE_CADENCE_AUDIT',callbacks=len(p),window_requested_shown=r['window_shown'],swap_identities=len(identities),statistics_hresult_counts=errors,positive_records=len(positive),scope='Exact ordered callback and epoch/QPC containment joins; successful submission IDs are not physical display proof. Positive statistics require refresh/QPC cadence and missing-ID analysis.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out)
