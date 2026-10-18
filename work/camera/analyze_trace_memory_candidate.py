import json,sys,copy
from pathlib import Path
def analyze(r):
 assert r['observer_stopped'] and not r['errors'] and r['thresholds_before']==r['thresholds_after'] and r['frozen_before']==r['frozen_after']
 rows=r['samples'];assert 2<=len(rows)<=r['capacity']
 assert all(a['time_ns']<b['time_ns'] for a,b in zip(rows,rows[1:]))
 assert all(x['private_bytes']>0 and x['working_set_bytes']>0 for x in rows)
 def stats(key):
  v=[x[key] for x in rows];return dict(first=v[0],last=v[-1],peak=max(v),minimum=min(v),first_to_last=v[-1]-v[0])
 return dict(result='PASS_BOUNDED_READ_ONLY_PARENT_MEMORY_OBSERVATION',target=r['target'],samples=len(rows),retained_span_seconds=(rows[-1]['time_ns']-rows[0]['time_ns'])/1e9,private_bytes=stats('private_bytes'),working_set_bytes=stats('working_set_bytes'),scope=r['scope']+' Retained sample count does not independently prove zero drops; first/last include startup/shutdown, no steady-state slope or ownership qualification.')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=analyze(r)
 bad=copy.deepcopy(r);bad['samples'][1]['time_ns']=bad['samples'][0]['time_ns']-1
 try:analyze(bad)
 except AssertionError:out['reverse_clock_negative_control']='PASS'
 else:raise AssertionError('Clock reversal accepted')
 bad=copy.deepcopy(r);bad['thresholds_after'][0]+=1
 try:analyze(bad)
 except AssertionError:out['collector_policy_negative_control']='PASS'
 else:raise AssertionError('Changed collector policy accepted')
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
