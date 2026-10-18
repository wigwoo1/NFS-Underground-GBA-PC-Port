import ctypes as C,struct,random,json
from pathlib import Path
from owned_graph_wall_sources import WallSource
from owned_continuous_wall_visibility import select_wall
from owned_wall_projection import native_helpers,reciprocal_table
rng=random.Random(4107);table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);native=native_helpers();ct=reciprocal_table(table);cases=0;near_cases=0
for i in range(1000):
 flags=rng.choice((0,2,0x2000));vertices=bytearray(136);struct.pack_into('<H',vertices,42,65535);struct.pack_into('<H',vertices,46,flags)
 wall=WallSource(1,0,bytes(vertices),bytes(64),bytes(8),bytes(32),b'',0,0,0);base=bytearray(32);struct.pack_into('<H',base,0,1)
 fb=bytearray(64);near=32;struct.pack_into('<2h',fb,8,120,80);struct.pack_into('<i',fb,16,near);struct.pack_into('<I',fb,28,256)
 values=(rng.randrange(-500,501),rng.randrange(-500,501),rng.randrange(-100,1001),rng.randrange(-100,1001),*(rng.randrange(-150,151) for _ in range(4)));bounds=(0,239,0,159)
 scratch=C.create_string_buffer(52);struct.pack_into('<4h',scratch,0,*values[:4]);struct.pack_into('<4h',scratch,8,*values[4:]);struct.pack_into('<H',scratch,48,flags)
 h=(C.c_uint32*4)();a=(C.c_uint32*4)();ok=native.nfs_visibility_wall_clip(scratch,h,a,near,flags,0,ct)
 expected=False
 if ok:
  assert ok==1
  params=(C.c_uint32*5)(256,120,80,0,239);assert native.nfs_visibility_wall_project(scratch,params,ct)
  nf=struct.unpack_from('<H',scratch.raw,48)[0];ys=struct.unpack_from('<4h',scratch.raw,8)
  expected=not nf&4 and not(ys[0]>=159 and ys[1]>=159 and ys[2]<0 and ys[3]<0)
 out=select_wall(wall,bytes(48),values,fb,bounds,base,table)
 assert out.visible==expected,(i,values,out,scratch.raw.hex())
 if expected:
  assert out.x==struct.unpack_from('<2h',scratch.raw) and out.y==ys and out.flags==nf,(i,out,ys)
 near_cases+=(values[2]<near)!=(values[3]<near);cases+=1
report=dict(result='PASS_CONTINUOUS_WALL_INTEGER_ORACLE',cases=cases,near_crossings=near_cases,scope='Random integer camera-space clipping/projection/frontface/vertical selection versus recovered native implementation; original fractional raster oracle pending.')
Path('work/camera/continuous-wall-integer-oracle-tests.json').write_text(json.dumps(report,indent=2));print(report)
