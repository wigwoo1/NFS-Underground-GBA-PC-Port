"""Twelve entire 4K frames, owner-thread async copy/poll; disk IO after shutdown."""
import ctypes as C,time,json,threading,hashlib
from pathlib import Path
import owned_return_execution_live_candidate as backend
import owned_native_transaction_worker_install_candidate as tx
from owned_uncovered_window_candidate import OwnedD3DConsumer
NAME='owned-d3d-full-worker-return-candidate.dll'
def load(self,path,*args,**kwargs):
 if Path(path).name in ('owned-d3d-call-profile-candidate.dll','owned-d3d-present-batch-candidate.dll','owned-d3d-native-transaction-candidate.dll','owned-d3d-return-execution-candidate.dll'):path=str(Path(path).with_name(NAME))
 result=C.CDLL(path,*args,**kwargs)
 if Path(path).name==NAME:backend.loads.append(result._name)
 return result
backend.Loader.CDLL=load
ns=dict(backend.namespace);exec(compile(backend.source.replace('owned-d3d-return-execution-candidate.dll',NAME),'full-scene-async-backend-init','exec'),ns);OwnedD3DConsumer.__init__=ns['init']
SIZE=3840*2160*4;START=300;COUNT=12
buffers=[C.create_string_buffer(SIZE) for _ in range(COUNT)]
# Commit every destination page before the live game, with identical full-frame coverage.
pretouch_begin=time.perf_counter_ns()
for buffer in buffers:C.memset(buffer,0xA5,SIZE)
pretouch_ns=time.perf_counter_ns()-pretouch_begin
rows=[];slots={};missed=[];not_ready=0
folder=Path('work/camera/prototype-runs')/('full-scene-async-'+str(time.time_ns()))
prepare_original=tx.Session.prepare;commit_original=tx.Session.commit_present

def prepare(self,owned,e,g,i):
 global not_ready
 d=self.consumer.d;assert Path(d._name).name==NAME
 capture=d.nf_d3d_full_async_capture;capture.argtypes=[C.c_uint,C.c_uint64];capture.restype=C.c_int
 poll=d.nf_d3d_full_async_poll;poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t];poll.restype=C.c_int
 for slot,row in list(slots.items()):
  begin=time.perf_counter_ns();rc=poll(slot,row['capture_id'],buffers[row['sequence']],SIZE);end=time.perf_counter_ns();assert rc in (0,3),rc
  row.setdefault('poll_attempts',[]).append([begin,end,rc])
  if rc==3:not_ready+=1;continue
  profile=(C.c_uint64*8)();getter=d.nf_d3d_full_worker_profile;getter.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t];assert getter(slot,row['capture_id'],profile,C.sizeof(profile))==0
  row.update(native_worker_profile=list(profile),poll_begin_ns=begin,poll_end_ns=end,poll_thread=threading.get_ident());del slots[slot]
 result=prepare_original(self,owned,e,g,i)
 if START<=i<START+COUNT:
  slot=next((x for x in range(3) if x not in slots),None)
  if slot is None:missed.append([e,g,i]);return result
  sequence=len(rows);assert sequence<COUNT;capture_id=sequence+1;begin=time.perf_counter_ns();assert capture(slot,capture_id)==0;end=time.perf_counter_ns()
  row=dict(identity=[e,g,i],sequence=sequence,capture_id=capture_id,slot=slot,width=3840,height=2160,capture_begin_ns=begin,capture_end_ns=end,thread=threading.get_ident(),backend=d._name)
  rows.append(row);slots[slot]=row
 return result

def commit(self,payload,e,g,i):
 result=commit_original(self,payload,e,g,i)
 for row in rows:
  if row['identity']==[e,g,i]:row.update(commit=result['commit'],native_result=result['native_result'],older=payload[2],newer=payload[3],alpha=payload[4])
 return result
tx.Session.prepare=prepare;tx.Session.commit_present=commit

def save():
 folder.mkdir()
 for row in rows:
  if 'poll_end_ns' in row:
   data=buffers[row['sequence']].raw;path=folder/(str(row['sequence'])+'.rgba');path.write_bytes(data);row.update(file=str(path),sha256=hashlib.sha256(data).hexdigest())
 manifest=dict(rows=rows,expected=COUNT,start_index=START,missed=missed,pending=len(slots),not_ready=not_ready,host_buffer_bytes=COUNT*SIZE,pretouch_ns=pretouch_ns,staging_capacity=3,scope='Twelve consecutive entire 3840x2160RGBA diagnostic target captures. Copy/poll owner-thread, hashes/files after shutdown. Observer costs may perturb cadence; not physical scanout or broad route fidelity.')
 (folder/'manifest.json').write_text(json.dumps(manifest,indent=2));print('FULL_SCENE_ASYNC',folder/'manifest.json',flush=True)
