from pathlib import Path
import struct
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-mesh-tests/inputs';out.mkdir(exist_ok=True);table=(base/'NFSUG-pc-road-math-tests/references/reciprocal.bin').read_bytes()
for path in (base/'NFSUG-pc-world-tests/references').glob('*.nsp'):
 raw=bytearray(path.read_bytes())
 if path.name.startswith('synthetic'):
  mode=int(path.stem.split('-')[-1]);world=struct.unpack_from('<I',raw,48)[0];light,size=struct.unpack_from('<2I',raw,72);raw[light+size-131072:light+size]=table;struct.pack_into('<d',raw,world+52,2);struct.pack_into('<d',raw,world+68,2)
  if mode>=9:
   camera=world+166;struct.pack_into('<i',raw,camera+8,16384);struct.pack_into('<i',raw,camera+8+8*4,16384)
 (out/path.name).write_bytes(raw)

# Polygon integration cases exercise both windings, concavity and near clipping.
original=(out/'synthetic-mode-0.nsp').read_bytes();sections=[]
for i in range(5):
 at,size=struct.unpack_from('<2I',original,36+i*12);sections.append(original[at:at+size])
shapes={'concave': [(-20,-20,128),(20,-20,128),(20,20,128),(0,0,128),(-20,20,128)],'near': [(-20,-20,32),(-20,20,128),(20,20,128),(20,-20,32)],'hidden':[(-20,-20,32),(-20,20,32),(20,-20,32)],'collinear':[(0,0,128),(1,1,128),(2,2,128)]}
shapes['concave-degenerate']=list(shapes['concave'])
shapes['concave'][3]=(0,-5,128)
shapes['concave-reverse']=list(reversed(shapes['concave']))
for name,points in shapes.items():
 c=len(points);surface=struct.pack('<3I',c,2,1)+b''.join(struct.pack('<3d',*v) for v in points)+b''.join(struct.pack('<2d',i/(c-1),i%2) for i in range(c))+bytes([5,10,15,255]*2)
 world=struct.pack('<2I',0x31444652,1)+surface+struct.pack('<4I',0x3149574e,1,0,0);parts=list(sections);parts[1]=world;raw=bytearray(original[:92]);struct.pack_into('<I',raw,8,92+sum(map(len,parts)))
 for i,part in enumerate(parts):struct.pack_into('<3I',raw,32+i*12,i+1,len(raw),len(part));raw+=part
 (out/('synthetic-'+name+'.nsp')).write_bytes(raw)
