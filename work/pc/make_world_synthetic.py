from pathlib import Path
import struct
out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-world-tests\synthetic');out.mkdir(exist_ok=True)
model=Path(r'C:\NFSUG-Workspace\NFSUG-pc-model-tests\references\synthetic-near.model').read_bytes()
for mode in range(11):
 c=3;w=2;h=1;pixels=2;wall=mode in [2,3,7,8];lit=mode in [3,8];planes=17 if lit else 1
 surface=struct.pack('<3I',c,w,h)+struct.pack('<9d',0,0,64,0,1,64,1,0,64)+bytes(c*16)+bytes([5,10,15,255]*pixels)
 if mode==0:metadata=b''
 elif wall:metadata=bytes([0,2]*planes)+(bytes([0,77]*planes) if mode in [7,8] else b'')
 else:
  metadata=bytes([0,77])
  if mode>=9:metadata+=struct.pack('<2I',1,4)+bytes(48)
  if mode in [5,6,9,10]:metadata+=struct.pack('<8I',3,1,2,int(mode in [6,10]),4,2,0,0)+bytes(256)
 world=struct.pack('<2I',0x31444652,1)+surface+struct.pack('<4I',0x3149574e,1,mode,len(metadata))+metadata
 light=struct.pack('<3I',0x314c464e,1,int(lit))+(struct.pack('<4I',0,15,w,h)+bytes(pixels*64) if lit else b'')+bytes(32768*4)
 identity=struct.pack('<2I',0x3149464e,2)+struct.pack('<10I',2 if wall else 1,1,2,3,4,3,5,6,7,8)+struct.pack('<2Id8H',0x3242464e,2,0.,1,239,2,158,0,240,0,160)
 sections=[model,world,struct.pack('<4I',0x314f464e,2,0xffffffff,0),light,identity];raw=bytearray(92);struct.pack_into('<8I',raw,0,0x3150534e,1,92+sum(map(len,sections)),5,1,1,1,0)
 for i,section in enumerate(sections):struct.pack_into('<3I',raw,32+i*12,i+1,len(raw),len(section));raw+=section
 (out/f'synthetic-mode-{mode}.nsp').write_bytes(raw)

