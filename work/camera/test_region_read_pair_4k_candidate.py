from pathlib import Path
path=Path('work/camera/test_prepared_pair_4k_candidate.py');source=path.read_text()
source=source.replace('import owned_d3d_call_profile_install_candidate\n','import owned_d3d_call_profile_install_candidate\nimport owned_ordered_render_tail_install_candidate\nimport owned_region_read_backend_install_candidate\n')
source=source.replace('import sys,json,ctypes as C,weakref','''import sys,json,ctypes as C,weakref
from owned_uncovered_window_candidate import OwnedD3DConsumer
original_render=OwnedD3DConsumer.render
region_results=[]
def render(self,s,readback=False):
 result=original_render(self,s,readback)
 if True:
  import numpy as np;full=C.create_string_buffer(3840*2160*4);assert self.d.nf_d3d_read(full,len(full))==0;reference=np.frombuffer(full,np.uint8).reshape(2160,3840,4)[:,:,:3]
  for x,y,w,h in [(0,600,3840,64),(0,1200,3840,64),(123,456,17,9),(3839,2159,1,1)]:
   out=C.create_string_buffer(w*h*4);assert self.d.nf_d3d_read_region(x,y,w,h,out,len(out))==0
   import numpy as np
   rgba=np.frombuffer(out,np.uint8).reshape(h,w,4)
   assert np.array_equal(rgba[:,:,:3],reference[y:y+h,x:x+w,:])
   region_results.append(dict(x=x,y=y,w=w,h=h))
 return result
OwnedD3DConsumer.render=render''')
source=source.replace('prepared-pair-4k-','region-read-pair-4k-')
namespace=dict(__name__='__main__',__file__=str(path));exec(compile(source,str(path),'exec'),namespace);region_results=namespace['region_results']
assert len(region_results)==20
print('PASS_ACTUAL_FULLSCENE_REGION_PARITY',len(region_results))


