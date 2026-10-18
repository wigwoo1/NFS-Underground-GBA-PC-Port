from pathlib import Path
import struct,json
from sample_owned_motion import PreparedMotionPair
from owned_portal_traversal import traverse
from owned_portal_pose_residual import correction
exec(compile(Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0],'queue_setup','exec'))
raw=(p/'owned-portal-graphs.bin').read_bytes();offset=0;graphs={}
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);offset+=32;assert h[6]==1;data=raw[offset:offset+h[5]];offset+=h[5];cursor=0;graph={};top,bottom=next(iter(scenes[h[1]]['graph'].values()))[1:]
 for i in range(h[4]):
  index,n,*_=struct.unpack_from('<4I',data,cursor);cursor+=64;graph[index]=(bytes(data[cursor:cursor+n*68]),top,bottom);cursor+=n*68
 graphs[h[1]]=graph
older,newer=8758,8762;
a=(p/'motion-actual-scanline-assets'/f'{older}-native-complete-frame.bin').read_bytes();b=(p/'motion-actual-scanline-assets'/f'{newer}-native-complete-frame.bin').read_bytes();pair=PreparedMotionPair(a,b)
source_refreshes={label:next(k for k,v in scenes.items() if v['matrix']==struct.unpack('<12i',pair.arguments[0]['camera_'+label])) for label in ('older','newer')}
assert graphs[source_refreshes['older']]==graphs[source_refreshes['newer']]
checks=[]
for alpha in (0,.25,.5,.75,1):
 scene=scenes[source_refreshes['newer' if alpha==1 else 'older']];_,camera,_=pair.sample(alpha)
 regions=traverse(graphs[source_refreshes['older']],scene['matrix'],scene['framebuffer'],scene['expected'][0],reciprocal,sampled_camera=camera,endpoint_correction=correction(pair,alpha))
 if alpha in (0,1):assert regions==scene['expected']
 else:assert all(0<=x[1]<=238 and 0<=x[2]<=238 for x in regions)
 checks.append(dict(alpha=alpha,regions=[list(x) for x in regions]))
r=dict(result='PASS_SAMPLED_COMPLETE_PORTAL_GRAPH',checks=checks,exact_endpoints=2,source_refreshes=source_refreshes,scope='Diagnostic continuous-camera analytic projection; intermediate rounding compatibility, transitions and GPU integration not verified.')
(p/'owned-sampled-graph-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],[(x['alpha'],len(x['regions'])) for x in checks])
