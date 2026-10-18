import ctypes as C,numpy as np,json,hashlib
from pathlib import Path
from owned_source_d3d_vertex_convert_consumer_candidate import OwnedD3DConsumer
c=OwnedD3DConsumer();d=c.d;d.nf_d3d_convert_vertices.argtypes=[C.c_void_p,C.c_uint,C.c_size_t,C.c_void_p,C.c_size_t]
try:
 base=np.asarray([0.,-0.,1.,-1.,1+2**-24,1+3*2**-24,2**-149,2**-150,1e20,-1e20],np.float64)
 rng=np.random.default_rng(1234);values=np.concatenate((base,rng.uniform(-1e8,1e8,9990))).reshape(1000,10)
 out=np.empty(values.shape,np.float32);assert d.nf_d3d_convert_vertices(values.ctypes.data,1000,values.nbytes,out.ctypes.data,out.nbytes)==0
 expected=values.astype(np.float32);assert out.tobytes()==expected.tobytes()
 for count,sbytes,obytes,source in [(1000,values.nbytes-1,out.nbytes,values.ctypes.data),(1000,values.nbytes,out.nbytes-1,values.ctypes.data),(65537,values.nbytes,out.nbytes,values.ctypes.data),(1000,values.nbytes,out.nbytes,None)]:
  out.fill(17);before=out.tobytes();assert d.nf_d3d_convert_vertices(source,count,sbytes,out.ctypes.data,obytes)==1;assert out.tobytes()==before
finally:c.close()
out=dict(result='PASS_NATIVE_VERTEX_CONVERSION_EDGES',double_values=10000,invalid_calls=4,expected_float_sha256=hashlib.sha256(expected.tobytes()).hexdigest(),scope='Finite source conversion including signedzero/subnormal/tie rounding and deterministic random coordinates; invalid ABI rejects before output mutation. Does not verify NaN payloads or alternate floating point rounding modes.')
Path('work/camera/prototype-runs/native-vertex-conversion-edges.json').write_text(json.dumps(out,indent=2));print(out['result'])
