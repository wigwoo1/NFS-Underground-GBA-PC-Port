from pathlib import Path
import ctypes as C,os,struct,json,hashlib,io
source=Path(__file__).parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-world-tests');refs=out/'references'
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-world.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int
def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
read=fn('nf_pc_world_decode',[P,S,S],P);free=fn('nf_pc_world_free',[P],None);info=fn('nf_pc_world_info',[P,C.POINTER(Q)]);surface_info=fn('nf_pc_world_surface_info',[P,U,C.POINTER(Q)]);surface_buffer=fn('nf_pc_world_surface_buffer',[P,U,U,C.POINTER(P),C.POINTER(S)]);world_buffer=fn('nf_pc_world_buffer',[P,U,C.POINTER(P),C.POINTER(S)]);command=fn('nf_pc_world_command',[P,U,C.POINTER(Q)])
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def check(w,path):
 global surfaces,compared,commands,peak
 stream=io.BytesIO(path.read_bytes())
 def number(fmt):return struct.unpack(fmt,stream.read(struct.calcsize(fmt)))
 n,models,ncommands=number('>3I');meta=(Q*4)();assert info(w,meta);assert list(meta[:3])==[n,models,ncommands];peak=max(peak,meta[3]);digests=[]
 for i in range(n):
  expected=number('>12Q');v=(Q*12)();assert surface_info(w,i,v) and tuple(v)==expected,(path.name,i,list(v),expected);modes[str(v[4])]=modes.get(str(v[4]),0)+1
  for kind in range(10):
   size,=number('>I');expected=stream.read(size);actual=blob(surface_buffer,w,i,kind);assert actual==expected,(path.name,i,kind,len(actual),size);compared+=size;digests.append(hashlib.sha256(actual).hexdigest())
  surfaces+=1
 for kind in range(3):
  size,=number('>I');expected=stream.read(size);actual=blob(world_buffer,w,kind);assert actual==expected,(path.name,'world',kind);compared+=size;digests.append(hashlib.sha256(actual).hexdigest())
 for i in range(ncommands):
  expected=number('>2Q');v=(Q*2)();assert command(w,i,v) and tuple(v)==expected;commands+=1
 assert not stream.read();v=(Q*12)(*[77]*12);assert not surface_info(w,n,v) and list(v)==[77]*12;assert not command(w,ncommands,v) and list(v)==[77]*12
 return meta[3],digests
def digest(w):
 v=(Q*4)();assert info(w,v);values=[blob(surface_buffer,w,i,k) for i in range(v[0]) for k in range(10)]+[blob(world_buffer,w,k) for k in range(3)];return [hashlib.sha256(b).hexdigest() for b in values]
surfaces=commands=compared=peak=0;modes={};owners=0
for path in sorted(refs.glob('*.nsp')):
 raw=path.read_bytes();caller=C.create_string_buffer(raw);w=read(caller,len(raw),64*1024*1024);assert w,path.name
 try:
  budget,before=check(w,path.with_suffix('.reference'));C.memset(caller,0,len(raw));assert digest(w)==before,'Caller mutation affected world';assert not read(raw,len(raw),budget-1);exact=read(raw,len(raw),budget);assert exact;free(exact);owners+=1
 finally:free(w)
raw=next(refs.glob('*.nsp')).read_bytes();cases=[]
def badword(at,value):b=bytearray(raw);struct.pack_into('<I',b,at,value);cases.append(bytes(b))
for at in [0,4,8,12,28,32]:badword(at,0xffffffff)
for i in range(5):badword(36+i*12,len(raw)+1);badword(40+i*12,len(raw)+1)
world=struct.unpack_from('<I',raw,48)[0];order=struct.unpack_from('<I',raw,60)[0];light=struct.unpack_from('<I',raw,72)[0];identity=struct.unpack_from('<I',raw,84)[0]
for at in [world,order,light,identity]:badword(at,0)
badword(world+4,129);badword(world+8,33);badword(world+12,0);badword(identity+8,9);badword(light+8,2)
b=bytearray(raw);struct.pack_into('<d',b,world+20,float('nan'));cases.append(bytes(b));b=bytearray(raw);b[order+12:order+16]=b[order+8:order+12];cases.append(bytes(b));cases.extend([raw[:-1],raw+b'x',raw[:91]])
# Exercise deeper metadata validation for modes absent from captured snapshots.
for mode,offset,value in [(5,2,4),(5,6,11),(5,26,32768),(5,2+32+3*8,1),(9,2,0),(9,6,3),(7,0,1),(7,2,1),(8,2,2)]:
 sample=(refs/f'synthetic-mode-{mode}.nsp').read_bytes();start=struct.unpack_from('<I',sample,48)[0]+8+12+3*40+2*4+16;b=bytearray(sample)
 if mode in (7,8):b[start+offset]=value
 else:struct.pack_into('<I',b,start+offset,value)
 cases.append(bytes(b))
for index,bad in enumerate(cases):w=read(bad,len(bad),64*1024*1024);assert not w,('Malformed accepted',index)
assert owners==28 and surfaces==399
result=dict(result='PASS_PC_WORLD_DATA_DECODER',owners=owners,actual_source_owners=17,synthetic_modes=11,surfaces=surfaces,commands=commands,compared_buffer_bytes=compared,modes=modes,malformed_rejected=len(cases),maximum_requested_bytes=peak,caller_mutation_isolated=True,exact_budget_and_short_budget_verified=True,all_material_lighting_geometry_order_bounds_match_java=True,world_projection_implemented=False,gpu_world_drawing=False,full_scene=False,full_scene_60fps=False,source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['source_frame.c','source_frame.h','source_world.c','source_world.h']},test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dll_sha256=hashlib.sha256((out/'source-world.dll').read_bytes()).hexdigest())
(out/'world-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
