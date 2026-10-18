# Exercise the real static cached packet reader via a test-only compiled shim.
from pathlib import Path
import ctypes as C,json,os,threading,hashlib
out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-direct-cached-tests')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
Info=C.CFUNCTYPE(I,P,C.POINTER(Q));BG=C.CFUNCTYPE(S,P,Q,U,P,S);Owner=C.CFUNCTYPE(S,P,Q,U,U,U,P,S);Take=C.CFUNCTYPE(S,P,Q,U,C.POINTER(P));TakeOwner=C.CFUNCTYPE(S,P,Q,U,U,U,C.POINTER(P));Release=C.CFUNCTYPE(None,P)
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('bg',P),('geom',P),('road',P),('wall',P),('proof',P),('owner',Q)]
def fn(name,args,result=I):f=getattr(d,name);f.argtypes=args;f.restype=result;return f
bind=fn('nf_pc_source_api_bind_owner',[P]);op=fn('nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P);probe=fn('nf_pc_test_cached_packet',[P,U,Q,U,U,U,P,S],S);close=fn('nf_pc_source_reader_close',[P],None);info=fn('nf_pc_source_reader_direct_cached_info',[P,P]);failure=fn('nf_pc_source_reader_last_failure',[P,P])
state=dict(data=b'owned cached packet bytes',size=None,write=None,queries=0,writes=0)
@Info
def layer(core,p):return 0
@BG
def background(core,e,r,p,n):return 0
@Owner
def cached(core,e,s,b,end,p,n):
 if not p:state['queries']+=1;return len(state['data']) if state['size'] is None else state['size']
 state['writes']+=1
 if state['write'] is not None:return state['write']
 if n<len(state['data']):return 0
 C.memmove(p,state['data'],len(state['data']));return len(state['data'])
@Take
def take(core,e,r,p):p[0]=None;return 0
@TakeOwner
def take_owner(core,e,s,b,end,p):p[0]=None;return 0
release_errors=[]
@Release
def release(p):release_errors.append(p)
addr=lambda f:C.cast(f,P).value
api=API(C.sizeof(API),1,addr(layer),addr(background),addr(cached),addr(cached),addr(cached),addr(cached),0);assert bind(C.byref(api));r=op(C.byref(api),4096,addr(take),addr(release),addr(take_owner),addr(release));assert r
key=(2,10,11,12,13);n=len(state['data']);sentinel=C.create_string_buffer(b'x'*(n+8));before=sentinel.raw
assert probe(r,*key,sentinel,n)==0 and sentinel.raw==before and state['writes']==0
assert probe(r,*key,None,0)==n
assert probe(r,3,*key[1:],sentinel,n)==0 and probe(r,2,10,99,12,13,sentinel,n)==0
assert probe(r,*key,sentinel,n-1)==0 and sentinel.raw==before and state['writes']==0
assert probe(r,*key,sentinel,n)==n and sentinel.raw[:n]==state['data']
assert probe(r,*key,sentinel,n)==0 and state['writes']==1
for kind in (0,1,5,99):assert probe(r,kind,*key[1:],None,0)==0
for size in (0,4097):
 state['size']=size;assert probe(r,*key,None,0)==0;assert probe(r,*key,sentinel,n)==0
state['size']=None
assert probe(r,*key,None,0)==n;state['write']=n-1
assert probe(r,*key,sentinel,n)==0
f=(Q*6)();assert failure(r,f) and list(f)==[2,10,11,12,13,n-1]
assert probe(r,*key,sentinel,n)==0
state['write']=None;assert probe(r,*key,None,0)==n
state['data']+=b'!';assert probe(r,*key,sentinel,n)==0
state['data']=state['data'][:-1];assert probe(r,*key,None,0)==n and probe(r,*key,sentinel,n)==n
wrong=[];counts=state.copy()
def other():
 v=(Q*3)(77,77,77);wrong.append(probe(r,*key,None,0)==0 and not info(r,v) and list(v)==[77]*3);close(r)
t=threading.Thread(target=other);t.start();t.join();assert wrong==[True] and state==counts
v=(Q*3)();assert info(r,v) and v[1]==2 and v[2]==2*n;close(r);assert not release_errors
result=dict(result='PASS_DIRECT_CACHED_QUERY_WRITE_PROTOCOL',query_required=True,full_key_required=True,short_capacity_does_not_call_writer=True,one_write_per_query=True,invalid_kind_rejected=True,zero_oversize_size_rejected=True,size_change_and_short_write_rejected=True,failure_metadata_exact=True,wrong_thread_does_not_mutate=True,no_scratch_used=True,dll_sha256=hashlib.sha256((out/'source-reader.dll').read_bytes()).hexdigest())
(out/'cached-protocol-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
