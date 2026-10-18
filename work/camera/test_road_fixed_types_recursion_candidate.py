"""Execute the actual recursive visit body with a two-node native-write fixture."""
import ast,inspect,struct,ctypes as C
from types import SimpleNamespace
import owned_endpoint_road_fixed_types_candidate as module
source=ast.parse(inspect.getsource(module.endpoint_road_span_candidates));visit=next(x for x in ast.walk(source) if isinstance(x,ast.FunctionDef) and x.name=='visit')
state=bytes(896);base=4096;state=bytearray(state);struct.pack_into('<I',state,20,base)
class Memory:
 def read(self,address,size):
  assert size==48;identifier=(address-base)//48;out=bytearray(48);struct.pack_into('<H',out,6,1 if identifier==0 else 65535);return bytes(out)
class Native:
 def nfs_visibility_region_reconstruct(self,state,record,read,context,table,edges,en,stream,sn):
  identifier=struct.unpack_from('<H',record)[0];assert en==1664 and sn==1536
  state[0]=bytes([identifier+1]);stream[0]=bytes([identifier+1]);return 1
namespace=dict(module.__dict__,memory=Memory(),closed=SimpleNamespace(graph=SimpleNamespace(context=bytes(state))),d=Native(),read=None,context=None,table=None,begin=lambda:None,finish=lambda *x:None)
exec(compile(ast.fix_missing_locations(ast.Module(body=[visit],type_ignores=[])),'actual-road-visit','exec'),namespace)
g=namespace['visit'](0,(0,0,240,0,160,0,0,65535));parent=next(g);child=next(g)
assert parent[2].raw[0]==1 and child[2].raw[0]==2 and parent[3].raw[0]==1 and child[3].raw[0]==2
assert C.addressof(parent[2])!=C.addressof(child[2]) and C.addressof(parent[3])!=C.addressof(child[3])
try:next(g)
except StopIteration:pass
else:raise AssertionError('Unexpected extra child')
print('PASS_ACTUAL_ROAD_VISIT_RECURSIVE_PRIVATE_BUFFERS')
