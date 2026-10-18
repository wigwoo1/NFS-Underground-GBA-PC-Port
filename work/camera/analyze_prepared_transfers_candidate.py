import json,sys,statistics
from pathlib import Path
r,t,p=[json.loads(Path(x).read_text()) for x in sys.argv[1:4]];assert not t['dropped'] and not p['dropped']
trans={(x[0],x[1],x[4]):x for x in t['rows']};prep={};checks=[]
for x in p['rows']:
 assert len(x)==21 and x[19]==0 and list(x[3:11])==sorted(x[3:11]);key=tuple(x[:3]);assert key not in prep;prep[key]=x
for s in r['presentation_samples']:
 if s.get('presentation_backend')!='dxgi_flip_sequential':continue
 key=(s['epoch'],s['generation'],s['display_index']);a=trans[key];b=prep.pop(key)
 assert a[12]==1 and a[8]<=s['sample_begin_ns']<=s['draw_complete_ns']<=b[3]<=b[10]<=a[9]<=a[10]<=s['native_committed_sample'][6]<=a[11]
 checks.append(dict(epoch=key[0],generation=key[1],index=key[2],draw_ms=(s['draw_complete_ns']-s['sample_begin_ns'])/1e6,transfer_ms=(b[10]-b[3])/1e6,present_transaction_ms=(a[11]-a[10])/1e6,transfer_end_relative_deadline_ms=(b[10]-a[5])/1e6))
assert checks
out=dict(result='PASS_EXACT_PREDEADLINE_TRANSFER_JOIN',checked=len(checks),uncommitted_preparations=len(prep),before_deadline=sum(x['transfer_end_relative_deadline_ms']<=0 for x in checks),summary={k:dict(median=statistics.median(x[k] for x in checks),maximum=max(x[k] for x in checks)) for k in ['draw_ms','transfer_ms','present_transaction_ms']},rows=checks,scope='Exact epoch/generation/index joins and separate draw/transfer/wait/commit containment; transfer timing may overrun deadline and is recorded, not assumed before it.')
Path(sys.argv[4]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
