"""Original fixed-point region transform using only owned raw ring/offset/camera."""
import struct

def signed(value):
 value &= 0xffffffff
 return value-0x100000000 if value&0x80000000 else value

def transform(ring,offsets,camera):
 n=len(ring)//68
 if not 0<n<=32 or len(ring)!=n*68 or len(offsets)!=n*32 or len(camera)!=48:raise ValueError('Incomplete transform inputs')
 m=struct.unpack('<12i',camera);out=bytearray(n*52)
 def put(at,value):struct.pack_into('<H',out,at,value&65535)
 for i in range(n):
  v=ring[i*68:(i+1)*68];o=offsets[i*32:(i+1)*32];x,z=struct.unpack_from('<2i',v);x=signed(x+m[9]);z=signed(z+m[11]);top=bottom=m[10]
  if struct.unpack_from('<H',v,42)[0]!=65535:
   dx,dz=struct.unpack_from('<2h',o);x=signed(x+dx);z=signed(z+dz);top=signed(top+struct.unpack_from('<h',o,8)[0]);bottom=signed(bottom+struct.unpack_from('<h',o,10)[0])
  cx=signed(x*m[0]+z*m[6])>>14;cz=signed(x*m[2]+z*m[8])>>14;at=i*52
  put(at,cx)
  for j,source,base in ((8,8,top),(12,10,bottom),(10,12,top),(14,14,bottom)):put(at+j,struct.unpack_from('<H',v,source)[0]+base)
  if cz>0x5fff:return 0,bytes(out)
  put(at+4,cz);put(at+40,v[60]<<8);put(at+42,v[61]<<8)
 for i in range(n):
  prev=((i-1)%n)*52;put(prev+2,struct.unpack_from('<H',out,i*52)[0]);put(prev+6,struct.unpack_from('<H',out,i*52+4)[0])
 return 1,bytes(out)

