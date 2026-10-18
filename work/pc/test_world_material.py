from pathlib import Path
import ctypes as C,os,struct,io,json,hashlib
source=Path(__file__).parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-world-material-tests')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'world-material.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int

def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
read=fn('nf_pc_world_decode',[P,S,S],P);world_free=fn('nf_pc_world_free',[P],None);make=fn('nf_pc_world_material',[P,U,S],P);free=fn('nf_pc_world_material_free',[P],None);info=fn('nf_pc_world_material_info',[P,P]);image=fn('nf_pc_world_material_image',[P,U,C.POINTER(P),C.POINTER(S)]);curve=fn('nf_pc_world_material_curve',[P,P]);columns=fn('nf_pc_world_material_columns',[P,U,P,S])
def upload(m,level):p=P();n=S();assert image(m,level,C.byref(p),C.byref(n));return p.value,C.string_at(p,n.value)
worlds=accepted=rejected=variants=compared=column_count=lit_count=curve_count=0;peak=0;modes={};state_alphas=set()
for path in sorted((out/'inputs').glob('*.nsp')):
 raw=path.read_bytes();world=read(raw,len(raw),64*1024*1024);assert world,path.name;stream=io.BytesIO((out/'references'/path.with_suffix('.material').name).read_bytes());held=[]
 def integer():return struct.unpack('>I',stream.read(4))[0]
 try:
  count=integer()
  for i in range(count):
   valid=integer();m=make(world,i,64*1024*1024)
   if not valid:assert not m,(path.name,i,'Accepted unsupported material');rejected+=1;continue
   assert m,(path.name,i,'Rejected valid material');expected=struct.unpack('>7I',stream.read(28));meta=(Q*8)();assert info(m,meta) and tuple(meta[:7])==expected,(path.name,i,list(meta),expected);peak=max(peak,meta[7]);modes[str(meta[3])]=modes.get(str(meta[3]),0)+1;lit_count+=meta[5];curve_count+=meta[6]
   levels=integer();images=[];pointer=None
   for level in range(levels):
    n=integer();gold=stream.read(n);address,actual=upload(m,level);assert actual==gold,(path.name,i,level,'Upload bytes');images.append(gold);compared+=n;variants+=1
    if pointer is None:pointer=address
    assert address==pointer,'More than one expanded variant buffer'
    if meta[5]:state_alphas.update(actual[3::4])
   expected_curve=None;column_refs=[]
   if meta[6]:
    expected_curve=stream.read(48);values=(C.c_double*6)();assert curve(m,values) and bytes(values)==expected_curve,(path.name,i,'Curve');widths=integer()
    for _ in range(widths):
     width=integer();gold=stream.read(width*4);values=(C.c_uint32*width)();assert columns(m,width,values,len(values)*4) and bytes(values)==gold,(path.name,i,width,'Columns');column_count+=width;column_refs.append((width,gold))
    sentinel=(C.c_uint32*2)(77,77);assert not columns(m,0,sentinel,8) and list(sentinel)==[77,77];assert not columns(m,2,sentinel,7) and list(sentinel)==[77,77]
   else:
    sentinel=(C.c_double*6)(*[77]*6);assert not curve(m,sentinel) and list(sentinel)==[77]*6
   for level in list(range(levels-1,-1,-1))+[0]:assert upload(m,level)[1]==images[level],'Variant switching changed bytes'
   assert not make(world,i,meta[7]-1);exact=make(world,i,meta[7]);assert exact;free(exact)
   p=P(123);n=S(456);assert not image(m,16,C.byref(p),C.byref(n)) and p.value==123 and n.value==456
   if not meta[5]:assert not image(m,1,C.byref(p),C.byref(n))
   held.append((m,images,expected_curve,column_refs));accepted+=1
  assert not stream.read() and not make(world,count,64*1024*1024)
 finally:world_free(world)
 for m,images,expected_curve,column_refs in held:
  try:
   for level,gold in enumerate(images):assert upload(m,level)[1]==gold,'World release changed material'
   if expected_curve:
    values=(C.c_double*6)();assert curve(m,values) and bytes(values)==expected_curve
    for width,gold in column_refs:values=(C.c_uint32*width)();assert columns(m,width,values,width*4) and bytes(values)==gold
  finally:free(m)
 worlds+=1
assert worlds==38 and accepted==406 and rejected==3 and variants==631 and state_alphas=={0,128,255}
# World packet alpha remains structurally valid; material preflight must reject it.
invalid_alpha=0
for name in ['synthetic-mode-0','synthetic-lit-rgba']:
 raw=bytearray((out/'inputs'/(name+'.nsp')).read_bytes());world_offset=struct.unpack_from('<I',raw,48)[0];corners=struct.unpack_from('<I',raw,world_offset+8)[0];raw[world_offset+8+12+corners*40+3]=128
 world=read(bytes(raw),len(raw),64*1024*1024);assert world
 try:assert not make(world,0,64*1024*1024);invalid_alpha+=1
 finally:world_free(world)
r=dict(result='PASS_PC_WORLD_MATERIAL',worlds=worlds,actual_source_owners=17,actual_surfaces=388,accepted=accepted,unsupported_rejected=rejected,invalid_alpha_rejected=invalid_alpha,lit_materials=lit_count,visible_shade_curves=curve_count,upload_variants=variants,compared_upload_bytes=compared,compared_shade_columns=column_count,modes=modes,maximum_retained_requested_bytes=peak,all_states_skip_zero_nonzero=True,one_expanded_buffer_reused=True,all_variants_curves_columns_byte_identical_to_java=True,world_release_lifetime_verified=True,exact_and_short_budgets_verified=True,source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['source_frame.c','source_frame.h','source_world.c','source_world.h','source_road.c','source_road.h','world_mesh.c','world_mesh.h','world_material.c','world_material.h']},test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dll_sha256=hashlib.sha256((out/'world-material.dll').read_bytes()).hexdigest(),gpu_world_drawing=False,full_scene=False,full_scene_60fps=False)
(out/'world-material-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
