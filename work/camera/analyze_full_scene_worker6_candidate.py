import json,sys,copy
from pathlib import Path
def analyze(r):
 assert len(r['rows'])==12 and not r['missed'] and r['pending']==0
 assert r['staging_capacity']==6 and r['host_buffer_bytes']==12*3840*2160*4
 assert r['close_resource_stats']==[0,0,0] and r['close_worker_stats']==[0,0,0]
 assert all(len(x['poll_attempts'])<=128 for x in r['rows'])
 rows=[]
 for x in r['rows']:
  a,b,c,d,e,f,worker,owner=x['native_worker_profile'];attempts=x['poll_attempts'];assert 0<a<=b<=c<=d<=e<=f<=x['poll_end_ns']
  assert worker!=owner and owner==x['thread']==x['poll_thread']
  assert attempts and attempts[-1][2]==0 and all(v[2]==3 for v in attempts[:-1]) and all(v[0]<=v[1] for v in attempts)
  assert any(v[0]<=a<=b<=v[1] for v in attempts)
  assert x['poll_begin_ns']<=e<=f<=x['poll_end_ns']
  rows.append(dict(identity=x['identity'],owner_poll_attempts=len(attempts),max_owner_poll_ms=max((v[1]-v[0])/1e6 for v in attempts),map_ms=(b-a)/1e6,worker_queue_ms=(c-b)/1e6,worker_copy_ms=(d-c)/1e6,copy_to_owner_unmap_ms=(e-d)/1e6,worker_thread=worker,owner_thread=owner))
 return dict(result='PASS_FULL_4K_WORKER6_OWNERSHIP_TIMING_CLEANUP',rows=rows,max_owner_poll_ms=max(x['max_owner_poll_ms'] for x in rows),max_worker_copy_ms=max(x['worker_copy_ms'] for x in rows),scope='Exact map/copy/completion/unmap timeline and distinct native CPU worker versus graphics owner, all polling attempts. Does not establish route fidelity, physical scanout or sustained60.')
r=json.loads(Path(sys.argv[1]).read_text());out=analyze(r);bad=copy.deepcopy(r);bad['rows'][0]['native_worker_profile'][6]=bad['rows'][0]['native_worker_profile'][7]
try:analyze(bad)
except AssertionError:out['same_thread_negative_control']='PASS'
else:raise AssertionError('Wrong thread accepted')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
