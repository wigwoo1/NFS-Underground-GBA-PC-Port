import ctypes as C,hashlib,json,time,threading
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession'];original_prepare=Session.prepare;original_present=Session.present
folder=Path('work/camera/prototype-runs')/('owned-sky-stage-'+str(time.time_ns()));folder.mkdir()
rows=[];slots={};count=0;missed=[];not_ready=0
buffers=[C.create_string_buffer(3240*64*4) for _ in range(3)];plane=C.create_string_buffer(240*160*4)
def prepare(self,owned,epoch,generation,index):
 global count,not_ready
 d=self.consumer.d;d.nf_d3d_async_skyband_capture.argtypes=[C.c_uint,C.c_uint64,C.c_uint];d.nf_d3d_async_skyband_poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t];d.nf_d3d_sky_input_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
 for slot,row in list(slots.items()):
  start=time.perf_counter_ns();rc=d.nf_d3d_async_skyband_poll(slot,row['capture_id'],buffers[slot],len(buffers[slot]));end=time.perf_counter_ns();assert rc in (0,3)
  if rc==3:not_ready+=1;continue
  data=buffers[slot].raw;(folder/row['pixel_file']).write_bytes(data)
  row.update(poll_begin_ns=start,poll_end_ns=end,poll_thread=threading.get_ident(),pixel_sha256=hashlib.sha256(data).hexdigest());del slots[slot]
 available=next((slot for slot in range(3) if slot not in slots),None)
 if 120<=count+1<168:
  assert available is not None
  y=[648,810,972,1134,1296,1440][(count+1-120)//8]
  d.nf_d3d_sky_stage_arm.argtypes=[C.c_uint,C.c_uint64,C.c_uint]
  assert d.nf_d3d_sky_stage_arm(available,count+1,y)==0
 result=original_prepare(self,owned,epoch,generation,index);count+=1
 if 120<=count<168:
  available=next((slot for slot in range(3) if slot not in slots),None)
  if available is None:missed.append(dict(prepare=count,index=index));return result
  assert self.pending==(epoch,generation,index) and list(result['publication'][:3])==[epoch,generation,index]
  sequence=count-120;y=[648,810,972,1134,1296,1440][sequence//8];begin=time.perf_counter_ns();stage_info=(C.c_uint64*4)();stage_phase=C.c_double();d.nf_d3d_sky_stage_info.argtypes=[C.c_void_p,C.c_void_p];assert d.nf_d3d_sky_stage_info(stage_info,C.byref(stage_phase))==0;assert list(stage_info[:3])==[available,count,y];end=time.perf_counter_ns()
  row=dict(epoch=epoch,generation=generation,index=index,capture_id=count,sequence=sequence,y=y,x=300,width=3240,height=64,capture_begin_ns=begin,capture_end_ns=end,thread=threading.get_ident(),backend=Path(d._name).name,publication=list(result['publication']),sky_weight=stage_phase.value,context_sky_weight=owned.context.draw.weight,sky_stage_capture_ns=stage_info[3],pixel_file=str(sequence)+'.rgba',present=None)
  for input_slot in range(2):
   assert d.nf_d3d_sky_input_copy(input_slot,plane,len(plane))==0;data=plane.raw;(folder/(str(sequence)+'.input'+str(input_slot)+'.rgba')).write_bytes(data);row['input'+str(input_slot)+'_sha256']=hashlib.sha256(data).hexdigest()
  rows.append(row);slots[available]=row
 return result
def present(self,epoch,generation,index):
 result=original_present(self,epoch,generation,index)
 row=next((r for r in rows if (r['epoch'],r['generation'],r['index'])==(epoch,generation,index)),None)
 if row is not None:row['present']=dict(status=result['status'],thread=threading.get_ident(),completed_ns=time.perf_counter_ns())
 return result
Session.prepare=prepare;Session.present=present
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
original_run=NativeSourceCommitAdapter.run
def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,**kwargs):
 result=original_run(self,owned,epoch,generation,older,newer,index,alpha,deadline,**kwargs)
 row=next((r for r in rows if (r['epoch'],r['generation'],r['index'])==(epoch,generation,index)),None)
 if row is not None:
  assert 'commit' not in row;row.update(source_older=older,source_newer=newer,alpha=alpha,deadline_ns=deadline,native_result=result['native_result'],commit=result['commit'])
 return result
NativeSourceCommitAdapter.run=run
def save():
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,missed=missed,pending=len(slots),not_ready=not_ready,total_prepares=count,scope='48 attempted captures in6bands,3reusable slots. Nonblocking native poll; file writing and copies still perturb timing. No skyexclusive/scanout proof.'),indent=2));print('ASYNC_SKYBAND_MANIFEST',folder/'manifest.json',flush=True)
