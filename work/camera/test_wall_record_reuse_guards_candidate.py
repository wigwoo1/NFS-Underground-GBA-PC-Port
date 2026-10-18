import struct,json
from dataclasses import replace
from pathlib import Path
from owned_graph_wall_sources import WallSource
from owned_scene_gpu_wall import encode_draws
from owned_sampled_graph_record_reuse_candidate import RecordCache
context=bytes(896);wall=WallSource(1,0,bytes(68*2),bytes(64),bytes(16),bytes(72),b'abc',0,3,123);region=(1,0,239,0,159,0,0);scratch=bytes(52);owner=RecordCache();checks=0

def check(ctx,w,r,s,allowed=False):
 global checks
 draw=((7,r,w,s),);expected=encode_draws(ctx,draw,allow_deferred=allowed);actual=owner.encode(ctx,draw,allow_deferred=allowed);assert actual==expected
 assert owner.bytes==sum(len(v[2][1]) for v in owner.records.values()) and owner.bytes<=8*1024*1024 and len(owner.records)<=256;checks+=1
 return actual
first=check(context,wall,region,scratch);assert check(context,wall,region,scratch)[0][1] is first[0][1]
for field in ('vertices','offsets','animation','texture'):
 original=getattr(wall,field);changed=bytes([original[0]^1])+original[1:];check(context,replace(wall,**{field:changed}),region,scratch);check(context,wall,region,scratch)
for index in (256,304,384):
 changed=context[:index]+b'Z'+context[index+1:];check(changed,wall,region,scratch);check(context,wall,region,scratch)
check(context,wall,(1,2,235,4,155,0,0),scratch)
deferred=bytearray(scratch);struct.pack_into('<H',deferred,48,2);deferred=bytes(deferred)
check(context,wall,region,deferred,True)
try:owner.encode(context,((7,region,wall,deferred),),allow_deferred=False)
except ValueError:checks+=1
else:raise AssertionError('Invalid deferred cache hit accepted')
for i in range(300):check(context,replace(wall,edge=i),region,scratch)
# Exercise the byte cap independently of the entry cap.
large=replace(wall,texture=bytes(65536),shift=10,height=64)
for i in range(150):check(context,replace(large,edge=i),region,scratch)
check(context,wall,region,scratch)
out=dict(result='PASS_WALL_RECORD_REUSE_GUARDS',checks=checks,final_entries=len(owner.records),final_record_bytes=owner.bytes,scope='Changed wall/context/clip/scratch/deferred guards, replacement accounting, entry and byte-cap eviction; sampled traversal separately tested.')
Path('work/camera/prototype-runs/wall-record-reuse-guards-20261009.json').write_text(json.dumps(out,indent=2));print(out)
