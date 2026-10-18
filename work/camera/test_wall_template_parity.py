from dataclasses import replace
import struct,json
from owned_graph_wall_sources import WallSource
from owned_scene_gpu_wall import encode_draws as prior
from owned_wall_encode_candidate import encode_draws as candidate,_local,BUDGET
wall=WallSource(1,0,bytes(136),bytes(64),bytes(8),bytes(32),bytes(64),0,10,0)
context=bytes(896);scratch=bytes(52);region=(1,0,239,0,159,0,0)
def outcome(fn,c,w,r,s):
 try:return ('value',fn(c,((0,r,w,s),)))
 except Exception as e:return ('error',type(e).__name__,str(e))
cases=[(context,wall,region,scratch),(bytearray(context),wall,region,scratch),(context,replace(wall,vertices=bytearray(wall.vertices)),region,scratch)]
for w in (replace(wall,vertices=b''),replace(wall,shift=-1),replace(wall,texture=bytes(65537))):
 for r in (region,(1,-1,239,0,159,0,0)):cases.append((context,w,r,scratch))
for s in (bytes(1),bytes(48)+struct.pack('<H',2)+bytes(2)):cases.append((context,wall,region,s))
for args in cases:assert outcome(prior,*args)==outcome(candidate,*args),args
for i in range(300):
 w=replace(wall,edge=i);assert candidate(context,((i,region,w,scratch),))==prior(context,((i,region,w,scratch),))
 assert len(_local.entries)<=128 and sum(x[5] for x in _local.entries.values())<=BUDGET
assert _local.bytes==sum(x[5] for x in _local.entries.values())
print(json.dumps(dict(result='PASS',error_cases=len(cases),eviction_cases=300,retained_bytes=sum(x[5] for x in _local.entries.values()))))
