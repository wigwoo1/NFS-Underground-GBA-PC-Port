import sys,json
from pathlib import Path
sys.path.insert(0,'work/camera')
from owned_complete_original_update_ledger_candidate import ProducerDeadlineRows
import owned_producer_caller_gap_candidate as caller
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('work/camera/prototype-runs/owned-native-1791596110817831300.json');r=json.loads(p.read_text());ledger=r['original_update_retention']['complete_original_updates'];rows=ledger['records'];assert ledger['dropped']==0 and ledger['total']==len(rows)==r['original_updates']
assert all(b['refresh']==a['refresh']+1 for a,b in zip(rows,rows[1:]));by={x['refresh']:x for x in rows};assert len(by)==len(rows) and all(by[x['refresh']]==x for x in r['original_update_samples'])
replay=ProducerDeadlineRows()
for x in rows:
 if 'preceding_caller' in x:
  c=x['preceding_caller'];caller.submission(c['submit_begin_ns'],c['submit_end_ns'])
 replay.append(x)
assert replay.stats()['complete_original_updates']['records']==rows
assert all(replay.complete_updates[-len(replay.rows)+i] is y for i,y in enumerate(replay.rows))
out=dict(result='PASS_COMPLETE_ORIGINAL_UPDATE_LEDGER_AND_NO_DECODE_REPLAY',updates=len(rows),first_refresh=rows[0]['refresh'],last_refresh=rows[-1]['refresh'],scope='Actual complete live updates plus recent equality; all actual records replayed through improved collector, immutable encoded strings reused. Recorder replay alone does not prove cadence improvement; consult the corresponding runtime audit.')
p.with_name(p.stem+'-complete-update-audit.json').write_text(json.dumps(out,indent=2));print(out)
