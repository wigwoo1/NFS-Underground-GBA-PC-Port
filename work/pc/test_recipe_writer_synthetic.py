from pathlib import Path
import os,ctypes as C,json,hashlib,struct
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-writer-tests')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'writer-build-report.json').read_text());assert sha(out/'recipe-writer.dll')==build['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-writer.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(n,args,res=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=res;return f
op=fn('nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P);free=fn('nf_pc_recipe_writer_free',[P],None);sample=fn('nf_pc_recipe_writer_cell',[P,U,U,P]);info=fn('nf_pc_recipe_writer_info',[P,P])
owner=(Q*5)(9,2,0,9,0);ordinal=(1<<40)+3;address=0x08000000;rows=[];samples=0

def fixture(kind,command,texture,shade=b'\0'):
 values=[b'\0']*15;material=bytearray(48);struct.pack_into('<HHI',material,36,0,4,address);values[3 if kind==1 else 4]=bytes(material);values[7 if kind==1 else 8]=texture;values[8 if kind==1 else 9]=bytes(512)
 if kind==1:values[13]=struct.pack('<17I',*command);values[14]=struct.pack('<10Q',0x3152524e,80,9,7,ordinal,1,0,0,0,0)
 else:values[12]=struct.pack('<20I',*command);values[13]=shade;values[14]=struct.pack('<8Q',2,64,9,7,1,address,65536,12)
 keep=[C.create_string_buffer(v) for v in values];blocks=(Block*15)(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(keep)]);return keep,blocks

def check(name,kind,command,texture,expected,shade=b'\0'):
 global samples
 keep,blocks=fixture(kind,command,texture,shade);w=op(owner,kind,ordinal,8,blocks,15,64*1024*1024);assert w,name
 try:
  meta=(Q*10)();assert info(w,meta) and meta[6]==ordinal and meta[7]==7 and meta[8]==8
  for x,y,want in expected:
   got=(Q*4)();assert sample(w,x,y,got) and tuple(got)==want,(name,x,y,list(got),want);samples+=1
 finally:free(w)
 rows.append(dict(name=name,samples=len(expected)))
command=[0]*17;command[5]=address;command[6]=0x06000000+20;command[7]=2;command[16]=1;texture=bytes([0,255])*8
check('road-byte-lanes-zero-and-duplicated-row',1,command,texture,[(20,0,(0,0,0,1)),(21,0,(1,255,255,2)),(22,0,(0,0,0,1)),(23,1,(1,255,255,2)),(19,0,((1<<64)-1,0,0,0)),(20,2,((1<<64)-1,0,0,0))])
command=list(command);command[1]=0x50000;command[10]=0x10000;command[7]=5;command[16]=0
check('road-noncontiguous-mask-accumulation',1,command,bytes(range(16)),[(20,0,(0,0,0,1)),(22,0,(2,2,2,2)),(24,0,(0,0,0,1)),(26,0,(2,2,2,2)),(28,0,(0,0,0,1))])
command=[0]*20;command[2]=120;command[4]=4;command[9]=address;command[11]=1<<15;command[17]=0x06000000+60;command[19]=3;texture=bytearray(65536);texture[:3]=bytes([0,1,255]);shade=bytearray([88]*4081);shade[0]=99;shade[16]=0;shade[4080]=17
check('wall-source-zero-skip-shaded-zero-opaque-index255',2,command,bytes(texture),[(60,0,((1<<64)-1,0,0,0)),(61,0,((1<<64)-1,0,0,0)),(60,1,(1,1,0,1)),(61,1,(1,1,0,1)),(60,2,(2,255,17,2)),(60,3,((1<<64)-1,0,0,0))],bytes(shade))
command=list(command);command[1]=1<<14;command[3]=2;command[4]=8;command[6]=1;command[7]=4;command[11]=0x20000;command[13]=0x40000;command[16]=0x7ffff;command[17]=0x06000000+80;texture=bytearray(65536);texture[6:8]=bytes([5,6])
check('wall-step-up-horizontal-offset-vertical-wrap-start-row',2,command,bytes(texture),[(80,1,(6,5,5,2)),(81,1,(6,5,5,2)),(80,2,(7,6,6,2)),(80,3,(6,5,5,2)),(80,0,((1<<64)-1,0,0,0))])
command[3]=1;keep,blocks=fixture(2,command,bytes(texture));assert not op(owner,2,ordinal,8,blocks,15,64*1024*1024)
r=dict(result='PASS_ORIGINAL_WRITER_ZERO_LANES_MASK_AND_WALL_STEP_RULES',cases=len(rows),samples=samples,rows=rows,ordinal_above32bits_preserved=True,wall_source_zero_skips_before_shading=True,nonzero_shaded_to_zero_is_opaque=True,malformed_stepup_shift_rejected=True,dll_sha256=sha(out/'recipe-writer.dll'),build_report_sha256=sha(out/'writer-build-report.json'),script_sha256=sha(Path(__file__)),core_opened=False,full_scene_60fps=False)
(out/'writer-synthetic-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
