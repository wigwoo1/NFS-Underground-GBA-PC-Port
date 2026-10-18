"""Exact native span comparison at aligned/unaligned and empty boundaries."""
import json,random
from pathlib import Path
from owned_immutable_tail_equal_candidate import equal
rng=random.Random(310);checks=0
for length in (0,1,7,15,16,17,31,32,33,255,4096,65536):
 tail=bytes(rng.randrange(256) for _ in range(length))
 for offset in (0,1,7,15):
  endpoint=b'P'*offset+tail;assert equal(endpoint,offset,tail);checks+=1
  if length:
   for index in set((0,length//2,length-1)):
    changed=tail[:index]+bytes([tail[index]^1])+tail[index+1:];assert not equal(endpoint,offset,changed);checks+=1
for args in ((b'abc',-1,b'abc'),(b'abc',4,b''),(b'abc',1,b'abc'),(bytearray(b'abc'),0,b'abc'),(b'abc',0,bytearray(b'abc'))):
 try:equal(*args)
 except ValueError:checks+=1
 else:raise AssertionError('Invalid immutable span accepted')
out=dict(result='PASS_NATIVE_IMMUTABLE_TAIL_EQUAL_BOUNDARIES',checks=checks,scope='Empty/aligned/unaligned0..65536byte exact comparisons and first/middle/last mutation rejection; invalid offset/size/mutable owner rejection. No performance or live qualification.')
Path('work/camera/prototype-runs/immutable-tail-equal-boundaries-20261009.json').write_text(json.dumps(out,indent=2));print(out)
