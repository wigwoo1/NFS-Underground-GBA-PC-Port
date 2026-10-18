import ctypes as C,numpy as np,json,hashlib
from pathlib import Path
from owned_source_d3d_fixed_quads_consumer_candidate import OwnedD3DConsumer
c=OwnedD3DConsumer();d=c.d;results=[]
d.nf_d3d_sky_quad.argtypes=[C.c_uint,C.c_float]
try:
 pixels=np.asarray([[x%256,y%256,(x+y)%256,255] for y in range(160) for x in range(240)],np.uint8)
 assert d.nf_d3d_texture(1001,240,160,pixels.ctypes.data,pixels.nbytes)==0
 assert d.nf_d3d_texture(1002,240,160,pixels.ctypes.data,pixels.nbytes)==0
 for layer in (0,1):
  for alpha in (0,0.125,0.333333333,0.5,0.875,1):
   images=[]
   for native in (False,True):
    assert d.nf_d3d_clear((C.c_float*4)(.1,.2,.3,1))==0
    if native:assert d.nf_d3d_sky_quad(layer,alpha)==0
    else:
     v=np.asarray([[x,y,u,v,0,1,1,1,1,alpha] for x,y,u,v in [(0,0,0,0),(240,0,1,0),(0,160,0,1),(240,0,1,0),(240,160,1,1),(0,160,0,1)]],np.float32)
     config=(C.c_float*8)(0,240,160,0,1,int(layer==0),.5,0);rect=(C.c_int*8)(0,0,3840,2160,300,0,3240,2160)
     assert d.nf_d3d_draw(v.ctypes.data,6,1001+layer,3,layer,config,rect)==0
    buf=C.create_string_buffer(3840*2160*4);assert d.nf_d3d_read(buf,len(buf))==0;images.append(buf.raw)
   assert images[0]==images[1]
   results.append(dict(layer=layer,alpha=alpha,sha256=hashlib.sha256(images[1]).hexdigest()))
 before=(C.c_uint64*4)();after=(C.c_uint64*4)();assert d.nf_d3d_stats(before)==0
 for layer,alpha in ((2,.5),(0,-.1),(1,1.1),(0,float('nan')),(1,float('inf'))):assert d.nf_d3d_sky_quad(layer,alpha)==1
 assert d.nf_d3d_stats(after)==0 and list(before)==list(after)
finally:c.close()
out=dict(result='PASS_SKY_FIXED_QUAD_GPU_PARITY',checks=results,invalid_inputs=5,scope='12 full4KRGBA native-target comparisons, synthetic texture both sky layers and fractionalalpha; not live sky asset fidelity/cadence/scanout.')
Path('work/camera/prototype-runs/native-sky-fixed-quad-parity.json').write_text(json.dumps(out,indent=2));print(out['result'])
