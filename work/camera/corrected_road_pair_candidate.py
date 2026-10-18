import ctypes as C,inspect,math,textwrap,ast,re
from pathlib import Path
import owned_sampled_road_camera as reference
import owned_sampled_road_sequence as sequence

library=C.CDLL(str(Path(__file__).with_name('road-corrected-pair-batch.dll')))
call=library.nf_road_corrected_pair
call.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_size_t];call.restype=C.c_int
stats=dict(native_calls=0,fallback_calls=0)

def corrected(world,a,b,poses,camera,alpha):
    # Exact immutable supported operands only. Every unsupported condition uses
    # original far-before-camera evaluation, preserving its errors and order.
    if isinstance(camera,C.Array) and camera._type_ is C.c_double and len(camera)==12:camera=tuple(camera)
    supported=type(world) is tuple and len(world)%3==0 and len(world)<=96 and type(alpha) in (int,float)
    supported=supported and all(type(m) is tuple and len(m)==12 and all(type(x) is int and -2147483648<=x<=2147483647 for x in m) for m in (a,b))
    supported=supported and type(poses) is tuple and len(poses)==2 and all(type(p) is tuple and len(p)==12 for p in (*poses,camera))
    if supported:
        supported=all(type(x) in (int,float) and math.isfinite(x) for p in (world,*poses,camera) for x in p) and math.isfinite(alpha) and 0<=alpha<=1
    if supported:
        n=len(world)//3;out=(C.c_double*(n*4))()
        status=call((C.c_double*len(world))(*world),n,(C.c_int32*12)(*a),(C.c_int32*12)(*b),(C.c_double*12)(*poses[0]),(C.c_double*12)(*poses[1]),(C.c_double*12)(*camera),alpha,out,n*4)
        if status==0:
            stats['native_calls']+=1
            return tuple(out[n*3:]),tuple(out[:n*3])
    stats['fallback_calls']+=1
    far=reference.sampled_road_far_depths(world,a,b,poses,camera,alpha)
    xyz=reference.sampled_road_camera(world,a,b,poses,camera,alpha)
    return far,xyz

source=textwrap.dedent(inspect.getsource(sequence.SampledRoadSequence.sample))
# Existing source-generated worker wrappers can expose their enclosing class
# to inspect. Extract only the actual sample method and retain its globals.
tree=ast.parse(source)
method=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='sample')
source=ast.get_source_segment(source,method)
marker=re.escape('far=sampled_road_far_depths(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha)')+r'\n[ \t]*'+re.escape('camera=sampled_road_camera(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha);')
assert len(re.findall(marker,source))==1
source=re.sub(marker,'far,camera=corrected(raw,self.ma,self.mb,self.portal.endpoints,pose,alpha);',source)
# inspect returns a method with one-space indentation.
source=textwrap.dedent(source)
namespace=dict(sequence.SampledRoadSequence.sample.__globals__,corrected=corrected)
exec(compile(source,__file__,'exec'),namespace)
sample=namespace['sample']
