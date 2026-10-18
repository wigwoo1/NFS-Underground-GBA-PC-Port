import json,sys
from pathlib import Path
from analyze_active_play_cadence import analyze
r=json.loads(Path(sys.argv[1]).read_text());d=json.loads(Path(sys.argv[2]).read_text())
assert r['result']=='SMOKE_COMPLETE' and not any(d['errors'])
committed={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')}
checks=[]
for ledger in d['reports']:
 assert ledger is not None and ledger['pending']==0
 allrows=ledger['completed']+ledger['omitted']+ledger['retired']
 assert len(allrows)==ledger['attempts'] and sorted(x['capture_id'] for x in allrows)==list(range(1,ledger['attempts']+1))
 for row in ledger['completed']:
  c=committed[row['display_index']]
  for key in ('epoch','generation','source_older','refresh','alpha','consumer_thread'):assert row[key]==c[key],key
  assert row['bytes']==3072
 transitions=[]
 for a,b in zip(ledger['completed'],ledger['completed'][1:]):
  if b['display_index']!=a['display_index']+1 or a['epoch']!=b['epoch']:continue
  transitions.append(dict(current=b['display_index'],changed=a['sha256']!=b['sha256'],gap_ms=(committed[b['display_index']]['native_committed_sample'][6]-committed[a['display_index']]['native_committed_sample'][6])/1e6))
 checks.append(dict(attempts=ledger['attempts'],completed=len(ledger['completed']),omitted=len(ledger['omitted']),retired=len(ledger['retired']),adjacent=len(transitions),changed_crops=sum(t['changed'] for t in transitions),transitions=transitions))
result=dict(result='PASS_LIVE_CAPTURE_ATTRIBUTION',ledgers=checks,cadence=analyze(r),scope='Final-target crop identity and diagnostic CPU commit cadence only. Crop may be foreground/static; no sky-only, physical scanout or sustained gameplay certification.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='ledgers'},indent=2));print([{k:v for k,v in x.items() if k!='transitions'} for x in checks])
