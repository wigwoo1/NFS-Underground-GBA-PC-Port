"""Bounded immutable model mesh loader for owned native scene draws."""
from dataclasses import dataclass
import struct,zlib
@dataclass(frozen=True)
class ModelMesh:
 model:int
 variant:int
 blocks:tuple
 @classmethod
 def decode(cls,encoded):
  raw=bytes(encoded)
  if len(raw)<60 or len(raw)>1024*1024:raise ValueError('Invalid mesh length')
  magic,model,variant,n,nf,corners,uv_count,size,crc=struct.unpack_from('<9I',raw)
  if magic!=0x31414d4e or variant>1 or not 0<n<=2048 or not 0<nf<=512 or not 0<uv_count<=4096 or size!=len(raw)-36 or zlib.crc32(raw[36:])!=crc:raise ValueError('Invalid mesh header')
  lengths=struct.unpack_from('<6I',raw,36)
  if lengths!=(40,n*6,nf,corners*2,corners*2,uv_count*4) or sum(lengths)!=len(raw)-60:raise ValueError('Invalid mesh blocks')
  blocks=[];cursor=60
  for length in lengths:blocks.append(raw[cursor:cursor+length]);cursor+=length
  desc,vertices,faces,vi,ui,uv=blocks
  if struct.unpack_from('<H',desc,36)[0]!=n or struct.unpack_from('<H',desc,34)[0]!=nf or sum(faces)!=corners or any(x<3 or x>32 for x in faces):raise ValueError('Invalid mesh faces')
  if any(x>=n for x in struct.unpack('<'+'H'*corners,vi)) or any(x>=uv_count for x in struct.unpack('<'+'H'*corners,ui)):raise ValueError('Invalid mesh indices')
  return cls(model,variant,tuple(blocks))
