"""Execute original ARM model XY/UV clip routine on owned synthetic rings."""
import sys,struct,json
from pathlib import Path
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
def clip(points,uv,rect,flags):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for address,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(address,size)
 u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x71b0c+0x6000])
 # Original startup seeds shared sequential indices used by clip scratch rings.
 for address in (0x03006bf0,):u.mem_write(address,struct.pack('<8H',*range(8)))
 n=len(points);poly=bytearray(32)
 for offset,value in [(0,0x02001000),(4,0x02002000),(8,0x02003000),(12,0x02004000),(20,n)]:struct.pack_into('<I',poly,offset,value)
 struct.pack_into('<H',poly,26,flags)
 for address,data in [(0x02001000,struct.pack('<'+'h'*2*n,*[v for p in points for v in p])),(0x02002000,struct.pack('<'+'H'*2*n,*[v for p in uv for v in p])),(0x02003000,struct.pack('<'+'H'*n,*range(n))),(0x02004000,struct.pack('<'+'H'*n,*range(n))),(0x02005000,poly),(0x02006000,struct.pack('<4i',*rect))]:u.mem_write(address,bytes(data))
 for reg,value in [(UC_ARM_REG_R0,0x02006000),(UC_ARM_REG_R1,0x02005000),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
 u.emu_start(0x03004270,0x03007000,count=100000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03007000
 p=bytes(u.mem_read(0x02005000,32));count=struct.unpack_from('<I',p,20)[0];assert count<=64
 xybase,uvbase,xi,ui=struct.unpack_from('<4I',p)
 ids=struct.unpack('<'+'H'*count,bytes(u.mem_read(xi,count*2)));tids=struct.unpack('<'+'H'*count,bytes(u.mem_read(ui,count*2)))
 return dict(status=u.reg_read(UC_ARM_REG_R0),points=[list(struct.unpack('<2h',bytes(u.mem_read(xybase+i*4,4)))) for i in ids],uv=[list(struct.unpack('<2H',bytes(u.mem_read(uvbase+i*4,4)))) for i in tids])
if __name__=='__main__':
 result=clip([[-10,10],[10,10],[10,30]],[[0,0],[100,0],[100,100]],[0,0,240,160],1)
 print(result);assert result==dict(status=0,points=[[0,10],[10,10],[10,30],[0,19]],uv=[[47,0],[100,0],[100,100],[47,47]])
 Path('work/camera/model-partial-clip-oracle.json').write_text(json.dumps(result,indent=2))


