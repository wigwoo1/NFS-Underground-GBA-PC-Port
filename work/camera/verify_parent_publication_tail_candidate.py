"""Exact owner and chronology checks for parent publication diagnostics."""
import json,sys,copy
from pathlib import Path
def validate(t,d):
 rows=t['rows'];assert rows and len(rows)==d['presentations'] and len(rows)<=t['capacity']
 owners={}
 for r in rows:
  k=tuple(r['identity']);assert k not in owners;owners[k]=r
  assert r['commit_ns']<=r['transaction_end_ns']<=r['append_begin_ns']<=r['append_end_ns'] and r['append_cycles']>=0
 for r in d['presentation_samples']:
  x=owners[r['epoch'],r['generation'],r['display_index']];assert x['commit_ns']==r['commit'][6] and x['transaction_end_ns']==r['transaction_end_ns']
 return dict(result='PASS_COMPLETE_PARENT_PUBLICATION_TAIL',rows=len(rows),retained_owner_matches=len(d['presentation_samples']),max_append_ms=max((x['append_end_ns']-x['append_begin_ns'])/1e6 for x in rows),committed_rows=sum(x['commit_ns']>0 for x in rows),max_commit_to_append_ms=max((x['append_begin_ns']-x['commit_ns'])/1e6 for x in rows if x['commit_ns']>0),scope=t['scope'])
if __name__=='__main__':
 t=json.loads(Path(sys.argv[1]).read_text());d=json.loads(Path(sys.argv[2]).read_text());out=validate(t,d)
 bad=copy.deepcopy(t);bad['rows'][1]['identity']=bad['rows'][0]['identity']
 try:validate(bad,d)
 except AssertionError:out['duplicate_owner_negative_control']='PASS'
 else:raise AssertionError('Duplicate accepted')
 bad=copy.deepcopy(t);bad['rows'][0]['append_end_ns']=bad['rows'][0]['append_begin_ns']-1
 try:validate(bad,d)
 except AssertionError:out['reverse_clock_negative_control']='PASS'
 else:raise AssertionError('Reverse clock accepted')
 Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out)
