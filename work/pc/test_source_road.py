from pathlib import Path
import ctypes as C,struct,os,json,hashlib,io,sys
out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-road-math-tests');refs=out/'references';source=Path(__file__).parent
dll_name=sys.argv[1] if len(sys.argv)>1 else 'source-road.dll'
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/dll_name))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;I=C.c_int;D=C.c_double

def f(name,args):v=getattr(dll,'nf_pc_road_'+name);v.argtypes=args;v.restype=I;return v
camera=f('camera',[P,S,P,P]);vertex=f('vertex',[P,D,P,U,U,U,P]);near=f('near',[P,D,D,P,U,U,U,I,P]);clip=f('clip',[P,P,U,P,S,P,C.POINTER(U)]);point=f('project_point',[P,P,P,U,U,P,P]);project_near=f('project_near',[P,P,P,D,P]);ring=f('project_ring',[P,P,U,P,S,P,S,P,P,C.POINTER(U)])
stream=io.BytesIO((refs/'cases.bin').read_bytes());table=(refs/'reciprocal.bin').read_bytes();assert len(table)==131072

def read(fmt):n=struct.calcsize(fmt);raw=stream.read(n);assert len(raw)==n;return struct.unpack(fmt,raw)
def ds(n):return (D*n)(*read('>'+str(n)+'d'))
def ints(n):return (I*n)(*read('>'+str(n)+'i'))
counts={};values=0;case=0
while stream.tell()<len(stream.getbuffer()):
 kind,=read('>I');counts[str(kind)]=counts.get(str(kind),0)+1;case+=1;v=(D*320)();n=U()
 if kind==1:raw=stream.read(56);p=ds(3);expected=ds(3);size=3;ok=camera(raw,len(raw),p,v)
 elif kind==2:
  depth,=read('>d');attrs=ints(2);shift,height,affine=read('>3I');expected=ds(2);size=2;ok=vertex(table,depth,attrs,shift,height,affine,v)
 elif kind==3:
  z0,z1=read('>2d');attrs=ints(4);shift,height,affine,znear=read('>4I');expected=ds(2);size=2;ok=near(table,z0,z1,attrs,shift,height,affine,znear,v)
 elif kind==4:
  count,=read('>I');points=ds(count*3);attrs=stream.read(288);expected_count,=read('>I');expected=ds(expected_count*5);size=expected_count*5;ok=clip(table,points,count,attrs,len(attrs),v,C.byref(n));assert n.value==expected_count,(case,'count')
 elif kind==5:
  p=ds(3);attrs=ds(2);shift,height=read('>2I');projection=ints(3);expected=ds(5);size=5;ok=point(table,p,attrs,shift,height,projection,v)
 elif kind==6:
  a=ds(5);b=ds(5);znear,=read('>d');expected=ds(5);size=5;ok=project_near(table,a,b,znear,v)
 elif kind==7:
  count,=read('>I');world=ds(count*3);attrs=stream.read(288);raw_camera=stream.read(56);projection=ints(3);expected_count,=read('>I');expected=ds(expected_count*5);size=expected_count*5;ok=ring(table,world,count,attrs,len(attrs),raw_camera,len(raw_camera),projection,v,C.byref(n));assert n.value==expected_count,(case,'count')
 else:raise AssertionError(kind)
 assert ok,(case,kind,'Rejected valid reference')
 actual=C.string_at(v,size*8);gold=bytes(expected)
 if actual!=gold:
  mismatches=[dict(index=i,native=v[i],java=expected[i]) for i in range(size) if struct.pack('<d',v[i])!=struct.pack('<d',expected[i])];raise AssertionError((case,kind,mismatches[:8]))
 values+=size
# Errors must leave all output values and ring count untouched.
rejected=0

def reject(call):
 global rejected
 v=(D*320)(*[77]*320);n=U(555);assert call(v,n)==0;assert list(v)==[77]*320 and n.value==555;rejected+=1
attrs=(I*4)(1,2,3,4);p=(D*3)(1,2,64);projection=(I*3)(120,80,64)
for depth in [float('nan'),0,32768]:reject(lambda v,n:vertex(table,depth,attrs,7,64,0,v))
for args in [(11,64,0),(7,3,0),(7,64,2),(7,2147483648,0)]:reject(lambda v,n:vertex(table,64,attrs,*args,v))
reject(lambda v,n:vertex(bytes(131072),64,attrs,7,64,0,v));reject(lambda v,n:near(table,100,101,attrs,7,64,0,64,v));reject(lambda v,n:near(table,-32769,100,attrs,7,64,0,64,v));reject(lambda v,n:camera(bytes(56),56,p,v));reject(lambda v,n:point(table,(D*3)(1,2,0),p,7,64,projection,v));reject(lambda v,n:project_near(table,(D*5)(1,2,100,3,4),(D*5)(5,6,101,7,8),64,v));reject(lambda v,n:clip(table,p,2,bytes(288),288,v,C.byref(n)));reject(lambda v,n:ring(table,p,2,bytes(288),288,bytes(56),56,projection,v,C.byref(n)))
r=dict(result='PASS_PC_SOURCE_ROAD_MATH',cases=case,case_counts=counts,captured_road_rings=86,compared_double_values=values,all_outputs_byte_identical_to_java=True,invalid_cases_rejected=rejected,invalid_output_unchanged=True,fixed_point_wrap_and_fractional_cases=True,source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['source_road.c','source_road.h']},test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dll_sha256=hashlib.sha256((out/dll_name).read_bytes()).hexdigest(),full_world_mesh=False,gpu_world_drawing=False,full_scene=False,full_scene_60fps=False)
(out/('road-math-report.json' if dll_name=='source-road.dll' else 'road-math-'+Path(dll_name).stem.replace('source-road-','')+'-report.json')).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
