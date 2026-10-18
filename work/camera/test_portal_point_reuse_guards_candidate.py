import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_portal_traversal import traverse as old
from owned_portal_point_reuse_candidate import traverse as new
setup=Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0];ns={};exec(compile(setup,'rawqueues','exec'),ns)
checks=[]
for refresh,scene in ns['scenes'].items():
 root=scene['expected'][0];args=(scene['graph'],scene['matrix'],scene['framebuffer'],root,ns['reciprocal'])
 cases=[('missing_root',({},*args[1:]),{}),('nan_camera',args,dict(sampled_camera=(float('nan'),)*12)),('capacity',args,dict(capacity=1)),('missing_link_viewport',args,dict(descriptor_links={root[0]:root[0]})),('missing_link_target',args,dict(descriptor_links={root[0]:999999},linked_viewport=(0,239)))]
 for name,a,kw in cases:
  values=[]
  for fn in (old,new):
   try:values.append(('return',fn(*a,**kw)))
   except (ValueError,IndexError,ZeroDivisionError) as e:values.append((type(e).__name__,str(e)))
  assert values[0]==values[1],(refresh,name,values)
  assert values[0][0]=='ValueError',(refresh,name,values)
  checks.append(dict(refresh=refresh,case=name,error=values[0][1]))
out=dict(result='PASS_PORTAL_REUSE_REJECTION_PARITY',checks=checks,count=len(checks),scope='Eight captured raw queues with missing descriptor, invalid camera, capacity and missing link guards; exact original/candidate rejection parity.')
p=Path('work/camera/prototype-runs/portal-point-reuse-guards-20261009.json');p.write_text(json.dumps(out,indent=2))
print(out['result'],len(checks))
