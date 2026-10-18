"""Existing native frame release spans retained in complete dequeue ledger."""
import json,sys
from pathlib import Path
def analyze(d):
 ledger=d['boundary_retention']['complete_dequeues'];assert ledger['dropped']==0
 rows=ledger['records'];out=[]
 for r in rows:
  span=r['previous_frame_free_ns'];cpu=r['previous_frame_free_execution']
  if span is None:continue
  a,b=span;assert a<=b<=r['loop_started_ns']
  assert cpu is not None and cpu['thread_cpu_ns']>=0 and cpu['thread_cycles']>=0
  out.append(dict(refresh=r['refresh'],release_begin_ns=a,release_end_ns=b,release_ms=(b-a)/1e6,after_release_to_loop_ms=(r['loop_started_ns']-b)/1e6,**cpu))
 assert out
 return dict(result='PASS_COMPLETE_FRAME_RELEASE_SCALARS',dequeues=len(rows),release_rows=len(out),max_release_ms=max(x['release_ms'] for x in out),largest=sorted(out,key=lambda x:x['release_ms'],reverse=True)[:10],scope='Existing release measurements, previous release associated with next completed dequeue. Postrelease gap may include idle notifications, not exclusively processing delay; thread CPU readings coarse. No scheduling policy change.')
if __name__=='__main__':
 d=json.loads(Path(sys.argv[1]).read_text());out=analyze(d)
 import copy
 bad=copy.deepcopy(d);r=next(x for x in bad['boundary_retention']['complete_dequeues']['records'] if x['previous_frame_free_ns']);r['previous_frame_free_ns'][1]=r['loop_started_ns']+1
 try:analyze(bad)
 except AssertionError:out['future_release_negative_control']='PASS'
 else:raise AssertionError('Future release accepted')
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='largest'})
