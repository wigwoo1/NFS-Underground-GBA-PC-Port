import struct,math
from types import SimpleNamespace
from pathlib import Path
from owned_wall_visibility_candidate import batch
from owned_continuous_wall_visibility import select_wall
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);v=bytearray(68);struct.pack_into('<H',v,42,65535);wall=SimpleNamespace(vertices=bytes(v),offsets=bytes(32));fb=bytearray(64);struct.pack_into('<2h',fb,8,120,80);struct.pack_into('<i',fb,16,512);struct.pack_into('<I',fb,28,16384)
def call(edge=(1.,2.,1000.,1000.,0.,0.,1.,1.),bounds=(0.,240.,0.,160.),table=r,framebuffer=bytes(fb)):return (wall,b'',edge,framebuffer,bounds,bytes((1,0)),table)
def check(calls):
 try:expected=tuple(select_wall(*c) for c in calls)
 except Exception as e:
  try:batch(calls)
  except Exception as actual:assert type(actual)==type(e) and str(actual)==str(e)
  else:raise AssertionError('Recovered failure lost')
 else:assert batch(calls)==expected
check([call(edge=(1e15,2e15,1000.,1000.,0.,0.,1.,1.))]);check([call(bounds=(-1e12,1e12,-1e12,1e12))]);check([call(table=list(r))]);check([call()]*4097)
fb2=bytearray(fb);struct.pack_into('<2h',fb2,8,140,90);check([call(),call(framebuffer=bytes(fb2))])
check([call(edge=(float('inf'),2.,1000.,1000.,0.,0.,1.,1.))]);check([call(edge=(float('nan'),2.,1000.,1000.,0.,0.,1.,1.))]);check([call(edge=(1.,2.,.5,.5,0.,0.,1.,1.)),call(edge=(float('nan'),2.,1000.,1000.,0.,0.,1.,1.))])
print('PASS: recovered domain/error parity for large coordinates/bounds,mutabletables,mixedframes,large batches,nonfinite/error precedence')
