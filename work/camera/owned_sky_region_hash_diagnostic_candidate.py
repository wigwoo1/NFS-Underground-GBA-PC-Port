"""Component-only readback hashes outside the sky destination rectangle."""
import ctypes as C,hashlib,numpy as np
from owned_uncovered_window_candidate import OwnedD3DConsumer
rows=[]
original=OwnedD3DConsumer.render
def render(self,*args,**kwargs):
 result=original(self,*args,**kwargs)
 rgba=C.create_string_buffer(3840*2160*4)
 assert self.d.nf_d3d_read(rgba,len(rgba))==0
 image=np.frombuffer(rgba,np.uint8).reshape(2160,3840,4)
 regions=dict(above=image[:594],below=image[1458:],left=image[:,:300],right=image[:,3540:])
 rows.append({name:hashlib.sha256(value.tobytes()).hexdigest() for name,value in regions.items()})
 return result
OwnedD3DConsumer.render=render
