from pathlib import Path
import sys,types,json
sys.path.insert(0,str(Path('work/camera').resolve()))
import owned_portal_traversal as module
from owned_portal_point_cache_candidate import traverse as candidate
fn=module.traverse;original=types.FunctionType(fn.__code__,fn.__globals__,fn.__name__,fn.__defaults__,fn.__closure__);calls=[]
def capture(*args,**kwargs):
 _portal_calls.append((args,dict(kwargs)));return _portal_original(*args,**kwargs)
fn.__globals__.update(_portal_calls=calls,_portal_original=original);fn.__code__=capture.__code__
try:
 env={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),env)
finally:fn.__code__=original.__code__
assert calls;rows=[]
def compare(args,kwargs,label,require_error=False):
 outcomes=[]
 for operation in (original,candidate):
  options=dict(kwargs);options['diagnostic_trace']=[]
  try:result=operation(*args,**options);outcomes.append(('ok',result,options['diagnostic_trace']))
  except Exception as error:outcomes.append(('error',type(error).__name__,str(error)))
 assert outcomes[0]==outcomes[1],label
 if require_error:assert outcomes[0][0]=='error',label
 rows.append(dict(case=label,result=outcomes[0][0]))
for i,(args,kwargs) in enumerate(calls):
 compare(args,kwargs,'captured-'+str(i))
 raw=dict(kwargs);raw['sampled_camera']=None;raw['endpoint_correction']=None;compare(args,raw,'raw-'+str(i))
 bad=dict(kwargs);bad['sampled_camera']=(0,)*11;compare(args,bad,'camera-length-'+str(i),True)
 bad=dict(kwargs);bad['sampled_camera']=(float('nan'),)+(0,)*11;compare(args,bad,'camera-nan-'+str(i),True)
 graph,matrix,fb,root,*tail=args
 bad_graph=dict(graph);bad_graph.pop(root[0]);compare((bad_graph,matrix,fb,root,*tail),kwargs,'missing-root-'+str(i),True)
 bad_graph=dict(graph);points,top,bottom=bad_graph[root[0]];bad_graph[root[0]]=(b'x',top,bottom);compare((bad_graph,matrix,fb,root,*tail),kwargs,'invalid-ring-'+str(i),True)
 bad=dict(kwargs);bad['capacity']=1;compare(args,bad,'capacity-'+str(i))
out=dict(result='PASS_EXACT_PORTAL_POINT_CACHE_DOMAINS',captured_calls=len(calls),cases=len(rows),sampled_calls=sum(x[1].get('sampled_camera') is not None for x in calls),rows=rows,scope='Captured and raw traversal queues/traces and identical invalid-input errors; component only.')
Path('outputs/nfsug-native-renderer/camera-research/portal-point-cache-domains-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],out['captured_calls'],out['cases'])
