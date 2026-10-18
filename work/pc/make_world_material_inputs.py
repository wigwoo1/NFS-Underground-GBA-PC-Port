from pathlib import Path
import struct
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-material-tests/inputs';out.mkdir(exist_ok=True)
for path in (base/'NFSUG-pc-world-mesh-tests/inputs').glob('*.nsp'):(out/path.name).write_bytes(path.read_bytes())
original=(out/'synthetic-mode-0.nsp').read_bytes();parts=[]
for i in range(5):at,n=struct.unpack_from('<2I',original,36+i*12);parts.append(original[at:at+n])
for name,mode,depths in [('lit-rgba',3,[32,128,128,32]),('lit-indexed',8,[128]*4),('lit-hidden',3,[32]*4),('lit-unsupported',3,[32,32,128,128])]:
 points=[(-20,-10,depths[0]),(20,-10,depths[1]),(20,10,depths[2]),(-20,10,depths[3])];surface=struct.pack('<3I',4,2,2)+b''.join(struct.pack('<3d',*p) for p in points)+b''.join(struct.pack('<2d',*p) for p in [(0,0),(1,0),(1,1),(0,1)])+bytes([10,20,30,255]*4)
 states=bytes([0,2,2,2])+b''.join(bytes([0,1 if level%2 else 2,2 if level%2 else 1,2]) for level in range(16));indices=bytes([0 if state!=2 else 1+(i%254) for i,state in enumerate(states)]) if mode==8 else b'';metadata=states+indices
 world=struct.pack('<2I',0x31444652,1)+surface+struct.pack('<4I',0x3149574e,1,mode,len(metadata))+metadata
 shades=b''.join(bytes([level*11%256,pixel*63,(level*17+pixel*3)%256,19]) for level in range(16) for pixel in range(4));light=struct.pack('<7I',0x314c464e,1,1,0,15,2,2)+shades+parts[3][-131072:]
 identity=struct.pack('<2I',0x3149464e,2)+struct.pack('<10I',2,1,2,3,4,3,5,6,7,8)+struct.pack('<2Id8H',0x3242464e,2,0.,0,240,0,160,0,240,0,160)
 sections=[parts[0],world,parts[2],light,identity];raw=bytearray(original[:92]);struct.pack_into('<I',raw,8,92+sum(map(len,sections)))
 for i,part in enumerate(sections):struct.pack_into('<3I',raw,32+i*12,i+1,len(raw),len(part));raw+=part
 (out/('synthetic-'+name+'.nsp')).write_bytes(raw)

