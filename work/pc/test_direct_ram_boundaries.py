"""Exercise exact candidate reader against bus reference using real mGBA memory.

Extra exports/counters exist only in a cloned diagnostic DLL, never the package.
"""
from pathlib import Path
import os,json,hashlib,shutil,subprocess,ctypes as C,random
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');candidate=base/'NFSUG-pc-direct-ram-core-tests';out=base/'NFSUG-pc-ram-boundary-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((candidate/'owned-core-build-report.json').read_text());assert receipt['core_sha256']==sha(candidate/'capture-host.dll')
for name,digest in receipt['staged_input_sha256'].items():assert sha(candidate/'source'/name)==digest
shutil.copytree(candidate/'source',source,dirs_exist_ok=True)
p=source/'observer.c';text=p.read_text(encoding='utf-8');start=text.index('static int native_surface_read(');end=text.index('\n}',start)+2;body=text[start:end]
direct='if(1) /* PC canonical RAM copy; all other ranges retain bus reads. */';assert body.count(direct)==1 and body.count('if(source){memcpy(out,source,size);')==1
reference=body.replace('native_surface_read(','pc_bus_reference(',1).replace(direct,'if(0)',1)
instrumented=body.replace('if(source){memcpy(out,source,size);','if(source){pc_boundary_copy_bytes+=size;pc_boundary_copy_calls++;memcpy(out,source,size);',1)
exports='''
__declspec(dllexport) int nf_pc_boundary_read(uint32_t address,void*out,size_t size,int reference){return reference?pc_bus_reference(NULL,address,out,size):native_surface_read(NULL,address,out,size);}
__declspec(dllexport) void nf_pc_boundary_copies(uint64_t out[2]){out[0]=pc_boundary_copy_bytes;out[1]=pc_boundary_copy_calls;}
'''
text=text[:start]+'static uint64_t pc_boundary_copy_bytes,pc_boundary_copy_calls;\n'+reference+'\n'+instrumented+'\n'+exports+text[end:];p.write_text(text,encoding='utf-8')
args=[arg.replace(str(candidate/'source'),str(source)).replace(str(candidate/'capture-host.dll'),str(out/'boundary-host.dll')) for arg in receipt['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
for key in ['NF_TEST_DIRECT_CAPTURE_RAM','NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_VERIFY_CAPTURE_RAM','NF_TEST_VERIFY_CAPTURE_ROM']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'boundary-host.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint32;Q=C.c_uint64;I=C.c_int
def fn(name,args,r=I):f=getattr(dll,name);f.argtypes=args;f.restype=r;return f
op=fn('nfa_core_open',[C.c_char_p],P);close=fn('nfa_core_close',[P],None);load=fn('nfa_core_load_state',[P,P,S]);read=fn('nf_pc_boundary_read',[U,P,S,I]);copies=fn('nf_pc_boundary_copies',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};h=op(os.fsencode(rom));assert h;data=state.read_bytes();assert load(h,data,len(data));assert fn('nfa_core_capture_enable',[P,I])(h,1);rng=random.Random(20261015);cases=[]
for low,high in [(0x02000000,0x02040000),(0x03000000,0x03008000)]:
 for address,size in [(low,0),(low,1),(low,high-low),(high-1,1),(high,0),(high,1),(high-1,2),(low-1,1),(low-1,2)]:cases.append((address,size))
 for _ in range(120):
  address=rng.randrange(low,high);cases.append((address,min(rng.randrange(1,4097),high-address)))
cases += [(0x02040000,32),(0x0207fff0,32),(0x03008000,32),(0x0300fff0,32),(0x05000000,512),(0x050001ff,1),(0x050001ff,2),(0x06000000,256),(0x06017fff,2),(0x08000000,256),(0x0a000000,32),(0x04000000,4),(0xffffffff,2),(0,1),(0x02000000,0x100000000)]
rows=[];copied=0
try:
 for address,size in cases:
  # Huge/overflow requests must reject before touching these small sentinels.
  allocation=size if size<=0x40000 else 32;a=C.create_string_buffer(b'\xa5'*(allocation+16));b=C.create_string_buffer(b'\xa5'*(allocation+16));old=(Q*2)();new=(Q*2)();copies(old)
  ra=read(address,a,size,0);rb=read(address,b,size,1);copies(new)
  assert ra==rb and a.raw==b.raw,(hex(address),size,ra,rb)
  assert a.raw[allocation:]==b'\xa5'*16+b'\0'
  canonical=any(low<=address and address+size<=high for low,high in [(0x02000000,0x02040000),(0x03000000,0x03008000)])
  expected=size if ra and canonical else 0;assert new[0]-old[0]==expected,(hex(address),size,'copy dispatch');assert new[1]-old[1]==int(bool(ra and canonical))
  copied+=expected;rows.append(dict(address=f'0x{address:08x}',size=size,accepted=bool(ra),direct_bytes=expected))
 assert read(0x02000000,None,1,0)==read(0x02000000,None,1,1)==0
 assert copied>0x48000 and sum(row['accepted'] for row in rows)>240
finally:close(h)
assert before=={str(p):sha(p) for p in [rom,state]}
r=dict(result='PASS_DIRECT_RAM_ACTUAL_CORE_BOUNDARIES',cases=len(rows),all_return_values_and_bytes_equal=True,direct_copy_dispatch_verified=True,canonical_bytes_compared=copied,output_guards_unchanged=True,null_output_rejected=True,candidate_core_sha256=sha(candidate/'capture-host.dll'),candidate_build_report_sha256=sha(candidate/'owned-core-build-report.json'),diagnostic_core_sha256=sha(out/'boundary-host.dll'),diagnostic_observer_sha256=sha(p),script_sha256=sha(Path(__file__)),rom_state_sha256=before,diagnostic_only=True,shipping_core_modified=False,rows=rows)
(out/'ram-boundary-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
