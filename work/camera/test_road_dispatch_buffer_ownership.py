import ctypes as C,threading,concurrent.futures,json
from pathlib import Path
import owned_road_dispatch_buffers_candidate as candidate
from owned_sampled_road_clip import Attributes
saved=candidate.fn
seen={};barrier=threading.Barrier(4)
def stub(scratch,camera,n,attributes,affine,left,right,base,count,table,commit,out,amount,projected,missing):
 out[0]=camera[0]
 for i in range(1,6):out[i]=float(i)
 amount._obj.value=1;projected._obj.value=n;missing._obj.value=0;return 1
candidate.fn=stub
try:
 def run(i):
  attrs=Attributes();attrs.count=3;camera=[float(i)]*9;first=candidate.clipped_camera_road(None,1,camera,attrs,(0,240,0,160),0,3,None);values=candidate._buffers.values;addresses=tuple(C.addressof(x) for x in values);barrier.wait();camera[0]=i+100.;second=candidate.clipped_camera_road(None,1,camera,attrs,(0,240,0,160),0,3,None);assert first['ring'][0]==float(i) and second['ring'][0]==i+100.;assert addresses==tuple(C.addressof(x) for x in candidate._buffers.values);return addresses
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:addresses=list(pool.map(run,range(4)))
 assert len({a[0] for a in addresses})==4
 candidate.fn=lambda *args:0
 attrs=Attributes();attrs.count=3
 try:candidate.clipped_camera_road(None,1,[0.]*9,attrs,(0,240,0,160),0,3,None)
 except ValueError:pass
 else:raise AssertionError('Failure accepted')
finally:candidate.fn=saved
out=dict(result='PASS',isolated_threads=4,stable_buffers=True,immutable_prior_ring=True,native_failure_rejected=True,scope='Stubbed synchronous ABI ownership/reuse checks; actual fullscene/pixel parity verified separately');Path('work/camera/road-dispatch-buffer-ownership-tests.json').write_text(json.dumps(out,indent=2));print(out)
