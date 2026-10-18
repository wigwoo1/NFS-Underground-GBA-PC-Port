import ctypes as C,inspect,struct,threading
from pathlib import Path
import owned_portal_traversal as reference
d=C.CDLL(str(Path(__file__).with_name('portal-coordinate-batch.dll')))
fn=d.nf_portal_edges
fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_double,C.c_uint32,C.c_int32,C.c_int,C.c_void_p,C.c_size_t];fn.restype=C.c_int
local=threading.local()
stats={'native_batches':0,'native_edges':0}
def reciprocal_table(values):
    if type(values) is not tuple or not 2<=len(values)<=65536:return None
    cached=getattr(local,'table',None)
    if cached is not None and cached[0] is values:return cached[1]
    if not all(type(value) is int and 0<=value<=0xffffffff for value in values):return None
    result=(C.c_uint32*len(values))(*values)
    local.table=(values,result)
    return result
def parent_edges(points,n,matrix,camera,correction,near,scale,center,reciprocal,flip):
    if n>32768:return None
    try:
        def point(value):
            x,z=struct.unpack_from('<2i',value)
            result=((x+camera[9])*camera[0]+(z+camera[11])*camera[6],(x+camera[9])*camera[2]+(z+camera[11])*camera[8])
            if correction is None:return result
            ra,rb,na,nb,alpha=correction
            a,b=reference.endpoint_delta(x,z,ra,na),reference.endpoint_delta(x,z,rb,nb)
            return tuple(result[k]+(1-alpha)*a[k]+alpha*b[k] for k in range(2))
        operands=[];indices=[];values={}
        for i in range(n):
            raw=points[i*68:(i+1)*68]
            if struct.unpack_from('<H',raw,48)[0]==65535:continue
            a=point(raw);b=point(points[((i+1)%n)*68:(((i+1)%n)+1)*68])
            values[i]=(a,b,None)
            if max(a[1],b[1])>0x6000:break
            operands.extend((*a,*b));indices.append(i)
        if not indices:return values
        table=reciprocal_table(reciprocal)
        if table is None:return None
        inputs=(C.c_double*len(operands))(*operands);out=(C.c_double*(len(indices)*6))()
        if fn(inputs,len(indices),table,len(reciprocal),near,scale,center,int(flip),out,len(indices)):return None
        stats['native_batches']+=1;stats['native_edges']+=len(indices)
        for position,index in enumerate(indices):
            row=out[position*6:position*6+6]
            a,b,_=values[index];values[index]=(a,b,None if not row[0] else (row[1],row[2],int(row[3]),row[4],row[5]))
        return values
    except (ValueError,OverflowError,TypeError,IndexError,struct.error):return None
source=inspect.getsource(reference.traverse)
needle='  for i in range(n if parent[6]<=4 else 0):'
assert source.count(needle)==1
source=source.replace(needle,'  batched=parent_edges(points,n,matrix,sampled_camera,endpoint_correction,near,scale,center,reciprocal,index==0) if sampled_camera is not None and parent[6]<=4 else None\n'+needle)
source=source.replace('   a=camera_point(point);b=camera_point(nextpoint)','   a,b,batch_edge=batched[i] if batched is not None else (camera_point(point),camera_point(nextpoint),None)')
source=source.replace('else fixed_continuous_edge(a,b,near,scale,center,reciprocal,index==0)','else (batch_edge if batched is not None else fixed_continuous_edge(a,b,near,scale,center,reciprocal,index==0))')
namespace=dict(reference.__dict__,parent_edges=parent_edges)
exec(compile(source,'portal-parent-native-batch','exec'),namespace)
traverse=namespace['traverse']
