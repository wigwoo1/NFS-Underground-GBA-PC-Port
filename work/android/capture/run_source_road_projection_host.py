"""C oracle for complete original source-road point/near/ring preparation."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,math,os,random,struct,subprocess
p=argparse.ArgumentParser()
for name in ('output','table','jdk','gcc'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True);sources=('road_camera_continuous.c','road_near_continuous.c','road_point_project_continuous.c','road_source_ring.c','road_source_attributes.h');hashes={}
for name in sources:
 data=(root.parent/'camera'/name).read_bytes();(a.output/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(command):
 r=subprocess.run(list(map(str,command)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
libpath=a.output/'source-road-reference.dll';run([a.gcc,'-shared','-O2',*[a.output/n for n in sources if n.endswith('.c')],'-o',libpath]);os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(libpath));D=C.POINTER(C.c_double);I=C.POINTER(C.c_int32);U=C.POINTER(C.c_uint32)
point=lib.nf_road_point_project_fractional;point.argtypes=[D,D,C.c_uint,C.c_uint,I,U,D];point.restype=C.c_int
near=lib.nf_road_near_continuous;near.argtypes=[D,D,C.c_double,U,D];near.restype=C.c_int
class Raw(C.Structure):_fields_=[('header',C.c_uint32*6),('offsets',C.c_int32*2),('attrs',C.c_int32*64)]
ring=lib.nf_road_source_ring;ring.argtypes=[D,C.c_uint,C.POINTER(Raw),I,I,U,D,C.c_uint,C.POINTER(C.c_uint)];ring.restype=C.c_int
original_table=a.table.read_bytes();table=(C.c_uint32*32768).from_buffer_copy(original_table);rng=random.Random(81304);identity=[16384,0,0,0,16384,0,0,0,16384,0,0,0];cases=[]
def add(kind,values,shift=6,height=128,affine=0,projection=None,matrix=None):cases.append((kind,shift,height,affine,values,projection or [120,80,100],matrix or identity))
for i in range(512):add(0,[[rng.uniform(-32000,32000),rng.uniform(-32000,32000),rng.uniform(1,32766),rng.randint(-2147483000,2147483000)+rng.random(),rng.randint(-2147483000,2147483000)+rng.random()]],rng.randrange(11),rng.randrange(2,2049),projection=[rng.randint(-100000,100000),rng.randint(-100000,100000),rng.randint(0,2147483647)])
for z in (1,1.25,63.9999,64,64.0001,32766.9999,32767,0,32767.1,float('nan')):add(0,[[10.5,-2.25,z,123.5,-84.25]])
for attr in (-2147483648,-2147483647.5,2147483646,2147483647,float('inf')):add(0,[[1,2,64,attr,0]])
for shift,height,scale in ((11,128,100),(6,1,100),(6,65536,100),(6,128,-1)):add(0,[[1,2,64,0,0]],shift,height,projection=[120,80,scale])
for i in range(256):
 a0=[rng.uniform(-30000,30000),rng.uniform(-30000,30000),rng.uniform(-100,63.9999),rng.uniform(-1000000,1000000),rng.uniform(-1000000,1000000)];b=[rng.uniform(-30000,30000),rng.uniform(-30000,30000),rng.uniform(64,20000),rng.uniform(-1000000,1000000),rng.uniform(-1000000,1000000)];add(1,[a0,b] if i%2 else [b,a0])
for z0,z1 in ((63.9,64.1),(63.99999,64),(63.2,64.01),(10,64),(63,64),(65,66),(-40000,65),(float('nan'),65)):
 a0=[-5.25,2,z0,-123.5,12.75];b=[10.5,-4,z1,256.5,-42.25];add(1,[a0,b]);add(1,[b,a0])
shapes=[ [(-30,-10,32),(30,-10,100),(5,0,100),(30,30,100),(-30,30,100)], [(-30,-10,64),(30,-10,64),(30,30,64),(-30,30,64)], [(-30,-10,10),(30,-10,20),(30,30,30),(-30,30,25)] ]
for affine in (0,1):
 for shape in shapes:
  for reverse in (False,True):
   points=list(reversed(shape)) if reverse else shape;add(2,[[*p,(i-2)*14932,(i%3-1)*20480] for i,p in enumerate(points)],2,4,affine)
for i in range(64):
 count=rng.randrange(3,15);values=[]
 for j in range(count):angle=j*2*math.pi/count;values.append([math.cos(angle)*30,math.sin(angle)*20,100+math.sin(angle)*80,rng.randint(-1000000,1000000),rng.randint(-1000000,1000000)])
 matrix=identity.copy();matrix[0]=rng.choice([15000,16384,18000]);matrix[8]=rng.choice([15000,16384,18000]);matrix[9]=rng.randint(-10,10);matrix[10]=rng.randint(-10,10);matrix[11]=rng.randint(-10,10);add(2,values,rng.randrange(8),rng.randrange(1,129)*2,i%2,matrix=matrix)
add(2,[[1,2,100,0,0],[2,3,100,0,0]])
payload=bytearray(struct.pack('>II',0x31505352,len(cases)));accepted=rejected=vertices=0;groups={}
for ci,(kind,shift,height,affine,values,projection,matrix) in enumerate(cases):
 amount=len(values);output=(C.c_double*320)(*([98765.5]*320));before=bytes(output);params=(C.c_int32*3)(*projection);mat=(C.c_int32*12)(*matrix);count=C.c_uint(7777)
 if kind==0:
  inputs=(C.c_double*5)(*values[0]);good=point(inputs,C.cast(C.byref(inputs,24),D),shift,height,params,table,output);written=int(bool(good))
 elif kind==1:
  a0=(C.c_double*5)(*values[0]);b=(C.c_double*5)(*values[1]);good=near(a0,b,64,table,output);written=int(bool(good))
 else:
  world=(C.c_double*(amount*3))(*(v for row in values for v in row[:3]));raw=Raw();raw.header[:]=[amount,shift,height,affine,0x08001000,0x02000002]
  for i,row in enumerate(values):raw.attrs[i*2]=int(row[3]);raw.attrs[i*2+1]=int(row[4])
  good=ring(world,amount,C.byref(raw),mat,params,table,output,64,C.byref(count));written=count.value if good else 0
 if not good:assert bytes(output)==before and (kind!=2 or count.value==7777),'Nonatomic C rejection';rejected+=1
 else:accepted+=1;vertices+=written
 groups[str(kind)]=groups.get(str(kind),0)+1;payload+=struct.pack('>8i',kind,shift,height,affine,amount,*projection)+struct.pack('>12i',*matrix)+b''.join(struct.pack('>5d',*row) for row in values)+struct.pack('>2i',bool(good),written)+struct.pack('>'+str(written*5)+'d',*list(output)[:written*5])
assert bytes(table)==original_table;fixture=a.output/'source-road-cases.bin';fixture.write_bytes(payload);classes=a.output/'classes';classes.mkdir(exist_ok=True);files=[root/'java/org/codex/nfsugpreview'/(n+'.java') for n in ('NativeRoadCamera','NativeRoadProjection')]+[root/'tests/org/codex/nfsugpreview/SourceRoadProjectionTest.java'];run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.SourceRoadProjectionTest',a.table,fixture]);print(stdout,flush=True)
for name,digest in hashes.items():assert hashlib.sha256((root.parent/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_SOURCE_ROAD_PROJECTION_C_PARITY','cases':len(cases),'accepted':accepted,'rejected':rejected,'output_vertices':vertices,'groups_point_near_ring':groups,'java_stdout':stdout.strip(),'reference_sha256':hashes,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'fixture_sha256':hashlib.sha256(payload).hexdigest(),'table_sha256':hashlib.sha256(original_table).hexdigest(),'scope':'Source point/near/raw-camera ring component; no mesh/GPU/Android runtime integration yet'};(a.output/'source-road-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
