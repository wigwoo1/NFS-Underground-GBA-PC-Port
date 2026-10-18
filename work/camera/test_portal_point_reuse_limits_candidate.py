from pathlib import Path
import struct,json
from sample_owned_motion import PreparedMotionPair
from owned_portal_traversal import traverse
from owned_portal_pose_residual import correction
setup=Path('work/camera/test_owned_sampled_graph.py').read_text().split('older,newer=')[0]
marker="top,bottom=next(iter(scenes[h[1]]['graph'].values()))[1:]"
assert setup.count(marker)==1
setup=setup.replace(marker,"\n if h[1] not in scenes:continue\n top,bottom=next(iter(scenes[h[1]]['graph'].values()))[1:]")
exec(compile(setup,'graph_setup','exec'))
from owned_portal_point_reuse_candidate import traverse
from owned_portal_traversal import traverse as reference_traverse
refs=[8758,8762,8766,8769,8773,8776,8780];checks=[]
for older,newer in zip(refs,refs[1:]):
 pair=PreparedMotionPair((p/'motion-actual-scanline-assets'/f'{older}-native-complete-frame.bin').read_bytes(),(p/'motion-actual-scanline-assets'/f'{newer}-native-complete-frame.bin').read_bytes())
 source={label:next(k for k,v in scenes.items() if v['matrix']==struct.unpack('<12i',pair.arguments[0]['camera_'+label])) for label in ('older','newer')}
 assert graphs[source['older']]==graphs[source['newer']]
 for endpoint,alpha,label in ((0,1e-8,'older'),(1,1-1e-8,'newer')):
  scene=scenes[source[label]];_,camera,_=pair.sample(alpha)
  result=traverse(graphs[source['older']],scene['matrix'],scene['framebuffer'],scene['expected'][0],reciprocal,sampled_camera=camera,endpoint_correction=correction(pair,alpha))
  reference=reference_traverse(graphs[source['older']],scene['matrix'],scene['framebuffer'],scene['expected'][0],reciprocal,sampled_camera=camera,endpoint_correction=correction(pair,alpha))
  assert result==reference
  expected=scene['expected'];assert [x[0] for x in result]==[x[0] for x in expected]
  error=max(abs(a[j]-b[j]) for a,b in zip(result,expected) for j in (1,2));assert error<.001,error
  checks.append(dict(older=older,newer=newer,endpoint=endpoint,error_pixels=error))
r=dict(result='PASS_RAW_PORTAL_ENDPOINT_LIMITS',pairs=6,limits=12,max_error_pixels=max(x['error_pixels'] for x in checks),checks=checks,scope='Camera-space residual interpolation preserves endpoint clipping limits across six captured pairs. Fractional visibility boundaries, world-wrap transitions and GPU integration unverified.')
(p/'prototype-runs/portal-point-reuse-limit-tests-20261009.json').write_text(json.dumps(r,indent=2));print(r['result'],r['max_error_pixels'])
