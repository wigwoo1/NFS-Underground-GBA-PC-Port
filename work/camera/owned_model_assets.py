"""Immutable native model topology and material blocks from owned source memory."""
import struct
from types import MappingProxyType

def model_asset_blocks(context,memory):
 if len(context)!=68:raise ValueError('Invalid owned model context')
 words=struct.unpack('<17I',context);descriptor=memory.read(words[3],40)
 count=struct.unpack_from('<H',descriptor,36)[0];faces=struct.unpack_from('<H',descriptor,34)[0]
 if not 0<count<=2048 or not 0<faces<=512:raise ValueError('Unsupported model topology size')
 def word(offset):return struct.unpack_from('<I',descriptor,offset)[0]
 sizes=memory.read(words[11]+word(28),faces)
 if any(n<3 or n>32 for n in sizes):raise ValueError('Invalid model face ring')
 corners=sum(sizes)
 if corners>4096:raise ValueError('Model corner capacity exceeded')
 vertices=memory.read(words[4]+word(0)*6,count*6)
 indices=memory.read(words[8]+word(4)*2,corners*2)
 uv_indices=memory.read(words[9]+word(24)*2,corners*2)
 if max(struct.unpack('<'+'H'*corners,indices))>=count:raise ValueError('Model vertex index outside source')
 maximum=max(struct.unpack('<'+'H'*corners,uv_indices))
 if maximum>4095:raise ValueError('Model UV capacity exceeded')
 uv_address=words[5]
 if struct.unpack_from('<H',descriptor,32)[0]&1:uv_address+=word(8)*4
 uv=memory.read(uv_address,(maximum+1)*4)
 shift,height=struct.unpack_from('<2H',context,56)
 if shift>10 or not 0<height<=1024:raise ValueError('Unsupported model texture dimensions')
 texture=memory.read(words[13],(1<<shift)*height)
 return MappingProxyType({1:bytes(descriptor),4:bytes(vertices),5:bytes(sizes),6:bytes(indices),7:bytes(uv_indices),8:bytes(uv),10:bytes(texture)})


def model_record_blocks(context,memory,matrix,projection,bounds,palette):
 if len(matrix)!=48 or len(projection)!=64 or len(bounds)!=4 or len(palette)!=512:raise ValueError('Invalid contextual model ownership')
 left,right,top,bottom=bounds
 # Original03005824 classifies empty/reversed intervals as outside.
 # Preserve those source rectangles; ownership does not imply visible pixels.
 if not all(isinstance(x,int) and -2147483648<=x<=2147483647 for x in bounds):raise ValueError('Invalid source model rectangle')
 assets=model_asset_blocks(context,memory);gpu_context=bytearray(68)
 gpu_context[56:60]=context[56:60];gpu_context[64:68]=context[64:68]
 blocks=[None]*12
 for index,data in assets.items():blocks[index]=data
 blocks[0]=bytes(gpu_context);blocks[2]=bytes(matrix);blocks[3]=bytes(projection)
 blocks[9]=struct.pack('<4i',left,top,right,bottom);blocks[11]=bytes(palette)
 return tuple(blocks)

def model_palette_equivalent(blocks,original):
 if len(blocks)!=12 or len(original)!=512:raise ValueError('Invalid model palette comparison')
 palette=blocks[11]
 return all(palette[i*2:i*2+2]==original[i*2:i*2+2] for i in set(blocks[10]))
