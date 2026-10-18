import ctypes as C,json
from pathlib import Path
from owned_source_segmented_draw_candidate import OwnedSourceDraw
import owned_draw_array_types_install_candidate as candidate
frame=bytes(40);camera=[0.0]*12;models=[0.0]*12;bounds=[0.0]*4
raw=[0]*12;normal=[0.0]*12;offsets=[0,1];mask=[1]
args=(frame,camera,models,bounds,1,raw,raw,normal,normal,.5,offsets,mask,1)
a=OwnedSourceDraw(*args);b=OwnedSourceDraw(*args)
for i in range(1,10):
 assert type(a.owners[i]) is type(b.owners[i])
 assert C.addressof(a.owners[i])!=C.addressof(b.owners[i])
 assert bytes(a.owners[i])==bytes(b.owners[i])
a.owners[1][0]=7
assert b.owners[1][0]==0
camera[0]=9
assert b.owners[1][0]==0 and a.owners[1][0]==7
for n in range(1,257):candidate.array_type(C.c_uint8,n)
assert candidate.array_type.cache_info().currsize<=128
assert a.owners[1][0]==7 and b.owners[1][0]==0
checks=0
for index,value in [(4,0),(9,float('nan')),(9,1.1),(12,32769)]:
 values=list(args);values[index]=value
 try:OwnedSourceDraw(*values)
 except ValueError:checks+=1
 else:raise AssertionError(index)
out=dict(result='PASS_PRIVATE_DRAW_ARRAY_TYPE_OWNERSHIP',independent_buffers=9,negative_guards=checks,cache=candidate.array_type.cache_info()._asdict(),scope='Exact type reuse, fresh buffers/input isolation, eviction preserves existing draws and original validation guards. No GC/cadence gain claim.')
Path('work/camera/prototype-runs/draw-array-types-ownership-20261009.json').write_text(json.dumps(out,indent=2));print(out)
