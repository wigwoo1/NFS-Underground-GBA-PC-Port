"""Independent queue construction over retained fractional portal operands."""
import sys,json,struct,math
from pathlib import Path
namespace={};source=Path('work/camera/analyze_live_fractional_portal_edges_candidate.py').read_text().split('checked=crossings=',1)[0];exec(compile(source,'independent-portal-arithmetic','exec'),namespace)
data=namespace['data'];graphs=namespace['graphs'];fixed=namespace['fixed'];ideal=namespace['ideal'];oracle=namespace['oracle'];path=Path(sys.argv[1])
counts=dict(near_rejected=0,aperture_rejected=0,parent_rejected=0,far_breaks=0,depth_limits=0,frontier_limits=0,linked_regions=0,merged_visits=0,near_crossings=0,root_changes=0);checks=[];max_error=0
for sample in data['samples']:
 alpha=sample['alpha']
 if alpha in (0,1):continue
 a,b=[graphs[k] for k in sample['graph_ids']];ma=struct.unpack_from('<12i',a.context,256);mb=struct.unpack_from('<12i',b.context,256);ea,eb=sample['endpoint_cameras'];cam=sample['sampled_camera'];root=struct.unpack_from('<8H',a.context,368)[:7];newroot=struct.unpack_from('<8H',b.context,368)[:7]
 if root[0]!=newroot[0]:counts['root_changes']+=1;raise AssertionError('Independent changing-root selection not implemented')
 nodes=a.graph()[0];fb=a.context[304:368];near=struct.unpack_from('<i',fb,16)[0];scale=struct.unpack_from('<I',fb,28)[0];center=struct.unpack_from('<h',fb,8)[0];top,bottom=struct.unpack_from('<2H',a.context,92)
 def point_camera(point):
  x,z=struct.unpack_from('<2i',point);value=ideal(x,z,cam);fa,fb=fixed(x,z,ma),fixed(x,z,mb);ia,ib=ideal(x,z,ea),ideal(x,z,eb)
  return tuple(value[k]+(1-alpha)*(fa[k]-ia[k])+alpha*(fb[k]-ib[k]) for k in range(2))
 queue=[list(root)];linked=False;cursor=0
 while cursor<len(queue):
  if len(queue)>20:counts['frontier_limits']+=1;break
  parent=queue[cursor];ring=nodes[parent[0]][0];n=len(ring)//68
  if parent[6]>4:counts['depth_limits']+=1
  else:
   for i in range(n):
    point=ring[i*68:(i+1)*68];target=struct.unpack_from('<H',point,48)[0]
    if target==65535:continue
    x,y=point_camera(point),point_camera(ring[((i+1)%n)*68:((i+1)%n+1)*68])
    if max(x[1],y[1])>0x6000:counts['far_breaks']+=1;break
    result=oracle(x,y,near,scale,center)
    if result is None:counts['near_rejected']+=1;continue
    left,right,flags,z,nz=result
    if cursor==0 and left>right:left,right=right,left
    if left>=right:counts['aperture_rejected']+=1;continue
    if right<parent[1] or left>=parent[2]:counts['parent_rejected']+=1;continue
    lo=2.0 if flags&8 else max(left,parent[1]);hi=238.0 if flags&16 else min(right,parent[2]);bits=parent[5]&128
    if struct.unpack_from('<H',point,46)[0]&0x800:bits=128
    if min(z,nz)>0x800:bits|=1
    assert len(queue)<256;queue.append([target,lo,hi,top,bottom,bits,parent[6]+1]);counts['near_crossings']+=bool(flags)
  target=a.descriptor_links.get(parent[0],65535)
  if not linked and target!=65535:
   view=sample['linked_viewports'][0];assert view is not None and target in nodes
   queue.append([target,*view,parent[3],parent[4],128,parent[6],parent[0]]);linked=True;counts['linked_regions']+=1
  cursor+=1
 # Independently group original visits by descriptor, retaining the first.
 visited={}
 for i,row in enumerate(queue[1:],1):
  if len(row)==7:visited.setdefault(row[0],[]).append(i)
 for indices in visited.values():
  if len(indices)<2:continue
  first=queue[indices[0]];first[1]=min(queue[i][1] for i in indices);first[2]=max(queue[i][2] for i in indices)
  for i in indices[1:]:queue[i][5]|=8;counts['merged_visits']+=1
 expected=sample['portal_regions'];assert len(queue)==len(expected),(sample['sample_id'],queue,expected)
 for original,recovered in zip(queue,expected):
  assert len(original)==len(recovered)
  for k in range(len(original)):
   if k in (1,2):error=abs(original[k]-recovered[k]);assert error<1e-9;max_error=max(max_error,error)
   else:assert original[k]==recovered[k],(sample['sample_id'],k,original,recovered)
 checks.append(dict(sample_id=sample['sample_id'],regions=len(queue)))
assert checks
out=dict(result='PASS_INDEPENDENT_CAPTURED_FRACTIONAL_PORTAL_QUEUES',samples=len(checks),regions=sum(c['regions'] for c in checks),max_bound_error=max_error,coverage=counts,checks=checks,scope='Independent integer-cell arithmetic and queue/merge construction match captured sampled regions. Stable-root captured intervals only; zero-count branches are unverified. Does not prove changing-root selection, scene fidelity or60fps scanout.')
path.with_name(path.stem+'-fractional-queues-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
