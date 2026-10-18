from pathlib import Path
import ctypes as C,hashlib,json,os,struct,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-model-context-refresh-tests';out.mkdir(exist_ok=True)
proof=base/'NFSUG-Android-Native-Wide-20261017/byteproof-results/model-byteproof.bin';raw=proof.read_bytes();h=struct.unpack_from('<64Q',raw)
assert h[0:3]==(0x31424d4e,1,len(raw)) and h[11:18]==(1,1,12,53585,1,1,1) and h[18:23]==(0,0,1,1,1)
parts=[raw[h[32+i*2]:h[32+i*2]+h[33+i*2]] for i in range(8)]
assert parts[0]==parts[1] and parts[4]==parts[5] and parts[6]==parts[7] and len(parts[6])==209757
r=json.loads((proof.parent/'byteproof-report.json').read_text());m=r['step518']['capture_context']['model_assembly'];assert m[2]==1 and m[3]==2
header=root/'work/camera/model_context_refresh.h';(out/'model_context_refresh.h').write_bytes(header.read_bytes())
(out/'wrapper.c').write_text('#include "model_context_refresh.h"\n__declspec(dllexport) int check(const NFModelContextRefresh*q,NFModelContextRefreshRead r,void*u){return nf_model_context_refresh_checked(q,r,u);}\n__declspec(dllexport) size_t input_size(void){return sizeof(NFModelContextRefresh);}\n')
cmd=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-static-libgcc',str(out/'wrapper.c'),'-o',str(out/'check.dll')]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(cmd,check=True,capture_output=True,env=env)
U=C.c_uint32;I=C.c_int32;B=C.c_uint8;Block=U*3
class Input(C.Structure):
 _fields_=[(name,C.c_uint64) for name in ['epoch','context_epoch','owned_epoch']]+[(name,U) for name in ['serial','context_serial','begin','frame','context_frame','context','context_address','object','context_object','camera','verified','expected','active','ready']]+[('owned_args',U*3),('count',U),('used',U),('context_bytes',C.POINTER(B)),('owned_bytes',C.POINTER(B)),('blocks',C.POINTER(Block)),('rotation',C.POINTER(I)),('owned_rotation',C.POINTER(I))]
context=(B*68).from_buffer_copy(parts[0]);owned=(B*len(parts[4])).from_buffer_copy(parts[4]);blocks=(Block*h[13]).from_buffer_copy(parts[3]);rotation=(I*12).from_buffer_copy(parts[2]);q=Input()
for name,value in dict(epoch=m[4],context_epoch=m[15],owned_epoch=m[21],serial=m[5],context_serial=m[16],begin=m[6],frame=m[7],context_frame=m[17],context=m[8],context_address=m[13],object=m[10],context_object=m[14],camera=m[9],verified=m[12],expected=m[19],active=m[18],ready=m[20],count=m[26],used=m[27]).items():setattr(q,name,value)
q.owned_args[:]=m[22:25];q.context_bytes=context;q.owned_bytes=owned;q.blocks=blocks;q.rotation=rotation;q.owned_rotation=rotation
records=[tuple(row) for row in blocks];calls=[];mode='normal'
READ=C.CFUNCTYPE(C.c_int,C.c_void_p,U,C.c_void_p,C.c_size_t)
@READ
def read(user,address,target,size):
 calls.append((address,size))
 if mode=='read_failure':return 0
 data=None
 if h[7]<=address and address+size<=h[7]+68:data=parts[1][address-h[7]:address-h[7]+size]
 else:
  for start,length,offset in records:
   if start<=address and address+size<=start+length:data=parts[5][offset+address-start:offset+address-start+size];break
 if data is None:return 0
 if mode=='context_changed' and address==h[7]:data=bytes([data[0]^1])+data[1:]
 if mode=='source_changed' and address!=h[7]:data=bytes([data[0]^1])+data[1:]
 C.memmove(target,data,size);return 1
lib=C.CDLL(str(out/'check.dll'));lib.check.argtypes=[C.POINTER(Input),READ,C.c_void_p];lib.check.restype=C.c_int;lib.input_size.restype=C.c_size_t;assert lib.input_size()==C.sizeof(Input)
assert lib.check(C.byref(q),read,None)==1;positive_reads=len(calls);tests=['real_scene114_byteexact_transition']
def reject(name,x):
 assert lib.check(C.byref(x),read,None)==0,name
 tests.append(name)
def clone():return Input.from_buffer_copy(bytes(q))
for field,value in dict(verified=0,expected=0,active=1,ready=0,epoch=3,context_epoch=3,owned_epoch=3,serial=115,context_serial=115,context=q.context+4,context_address=q.context_address+4,object=q.object+4,context_object=q.context_object+4,camera=q.camera+4,frame=q.context_frame,context_frame=q.context_frame-1,begin=q.context_frame+1,count=0,used=0).items():
 x=clone();setattr(x,field,value);reject(field,x)
for name,value in [('count',129),('used',262145),('frame',q.context_frame-1),('context_frame',0xffffffff)]:
 x=clone();setattr(x,name,value);reject(name+'-bounds',x)
for i in range(3):
 x=clone();x.owned_args[i]^=4;reject('owned-arg-'+str(i),x)
changed=(I*12).from_buffer_copy(bytes(rotation));changed[7]^=1;x=clone();x.rotation=changed;reject('changed-rotation',x)
for name in ['context_bytes','owned_bytes','blocks','rotation','owned_rotation']:
 x=clone();setattr(x,name,None);reject('null-'+name,x)
for mode in ['read_failure','context_changed','source_changed']:reject(mode,clone())
mode='normal'
bad=(Block*h[13]).from_buffer_copy(parts[3]);bad[1][2]+=1;x=clone();x.blocks=bad;reject('noncontiguous-owned-layout',x)
bad=(Block*h[13]).from_buffer_copy(parts[3]);bad[0][1]=0xffffffff;x=clone();x.blocks=bad;reject('owned-range-overflow',x)
bad=(Block*h[13]).from_buffer_copy(parts[3]);bad[-1][1]-=1;x=clone();x.blocks=bad;reject('incomplete-owned-coverage',x)
assert lib.check(C.byref(q),read,None)==1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(result='VERIFIED_ACTUAL_MODEL_INPUTS_AND_REFRESH_REVALIDATION_CONTROLS',checks=len(tests)+1,cases=tests,source_blocks=12,source_bytes=53585,exact_geometry_bytes=209757,geometry_sha256=hashlib.sha256(parts[6]).hexdigest(),positive_reader_calls=positive_reads,helper_sha256=sha(header),proof_sha256=sha(proof),test_sha256=sha(Path(__file__)),compile_command=cmd,limits='Host actual-fixture component only; integrated Android source coverage, GPU, pacing and device tests remain separate.')
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
