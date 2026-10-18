from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
class Action(C.Structure):_fields_=[('kind',C.c_uint32),('pass_index',C.c_uint32),('mask',C.c_uint32),('record',C.c_uint8*16)]
Expand=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p);Emit=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p)
class Executor(C.Structure):_fields_=[('expand',Expand),('emit',Emit),('user',C.c_void_p)]+[(key,C.c_uint) for key in ('depth','regions','actions','failed','max_depth','max_regions')]
begin=d.nf_region_executor_begin;begin.argtypes=[C.c_void_p,Expand,Emit,C.c_void_p,C.c_uint,C.c_uint];execute=d.nf_region_execute;execute.argtypes=[C.c_void_p,C.c_void_p,C.c_uint];queue=d.nf_region_execute_queue;queue.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
mode='normal';trace=[];entries=[]
def rec(index):return struct.pack('<8H',index,0,240,0,158,0,0,65535)
@Expand
def expand(ctx,record,pas,out,capacity,count):
 index=struct.unpack('<H',C.string_at(record,2))[0];entries.append((index,pas))
 if mode=='expand_fail':return 0
 specs=[]
 if mode=='bad_count':C.cast(count,C.POINTER(C.c_uint))[0]=516;return 1
 if mode=='bad_kind':specs=[(5,index)]
 elif mode=='cycle':specs=[(2,index)]
 elif index==0 and pas==0:specs=[(1,index),(2,1),(3,index),(4,index)]
 elif index==0:specs=[(3,index)]
 else:specs=[(1,index)]
 actions=(Action*len(specs))()
 for i,(kind,child) in enumerate(specs):actions[i].kind=kind;actions[i].pass_index=0 if kind==2 else pas;actions[i].mask=1 if kind==4 else 0;actions[i].record[:]=rec(child)
 C.memmove(out,actions,C.sizeof(actions));C.cast(count,C.POINTER(C.c_uint))[0]=len(specs);return 1
@Emit
def emit(ctx,executor,invocation,action):
 a=C.cast(action,C.POINTER(Action)).contents;trace.append((invocation,a.kind))
 if mode=='emit_fail':return 0
 if a.kind==3 and a.pass_index==0:return execute(executor,rec(2),0)
 return 1
owner=Executor();assert begin(C.byref(owner),expand,emit,None,8,100);assert queue(C.byref(owner),rec(0),1);assert entries==[(0,0),(1,0),(2,0),(0,1)] and trace==[(0,1),(1,1),(0,3),(2,1),(0,4),(3,3)] and owner.depth==0
failures=0
for mode in ('expand_fail','bad_count','bad_kind','emit_fail','cycle','region_budget'):
 trace.clear();entries.clear();assert begin(C.byref(owner),expand,emit,None,4,1 if mode=='region_budget' else 100)
 assert not execute(C.byref(owner),rec(0),0) and owner.failed and owner.depth==0
 before=bytes(owner);assert not execute(C.byref(owner),rec(0),0) and bytes(owner)==before;failures+=1
report=dict(result='PASS',native_depth_first_regions=4,ordered_emits=6,terminal_failure_cases=failures,scope='Root two-pass ordering, static and object reentry, bounded recursion/region count, invalid plans and callback failure; partial assembly must be discarded on failure.')
(p/'region-executor-tests.json').write_text(json.dumps(report,indent=2));print(report)
