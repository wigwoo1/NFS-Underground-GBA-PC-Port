import random,struct,json,time,statistics,sys,runpy
from pathlib import Path
from types import SimpleNamespace
from owned_continuous_wall_visibility import select_wall
from owned_wall_visibility_candidate import batch
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);rng=random.Random(61006);fb=bytearray(64);struct.pack_into('<2h',fb,8,120,80);struct.pack_into('<i',fb,16,512);struct.pack_into('<I',fb,28,16384);calls=[]
for _ in range(5000):
 v=bytearray(68);o=bytearray(32);struct.pack_into('<H',v,42,rng.choice((0,65535)));struct.pack_into('<H',v,46,rng.choice((0,1,2,8192,8194)));struct.pack_into('<H',o,14,rng.choice((0,1)))
 wall=SimpleNamespace(vertices=bytes(v),offsets=bytes(o));edge=tuple(rng.uniform(-30000,30000) for _ in range(8));bounds=(0.,240.,0.,160.);call=(wall,b'',edge,bytes(fb),bounds,struct.pack('<H',rng.choice((0,1))),r)
 try:expected=select_wall(*call)
 except ValueError as e:
  try:batch([call])
  except ValueError as actual:assert str(actual)==str(e)
  else:raise AssertionError('Invalid domain accepted')
 else:assert batch([call])[0]==expected
print('PASS:5000 visibility/flags/near/viewport/vertical comparisons including error parity')
