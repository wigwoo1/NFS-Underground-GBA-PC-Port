import ctypes as C,hashlib,json,time,threading,os
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession'];original_prepare=Session.prepare;original_present=Session.present
folder=Path('work/camera/prototype-runs')/('owned-deferred-sky-coverage-'+str(time.time_ns()));folder.mkdir()
START=int(os.environ.get("NFSUG_SKY_CAPTURE_START","120"));assert 1<=START<=7000
rows=[];slots={};count=0;missed=[];not_ready=0
payloads={};payload_bytes=0
def retain(name,data):
 global payload_bytes
 assert name not in payloads and len(payloads)<288
 assert payload_bytes+len(data)<=160*1024*1024
 payloads[name]=data;payload_bytes+=len(data)
buffers=[C.create_string_buffer(3240*64*4) for _ in range(12)];plane=C.create_string_buffer(240*160*4)
def prepare(self,owned,epoch,generation,index):
 global count,not_ready
 d=self.consumer.d;d.nf_d3d_async_skyband_capture.argtypes=[C.c_uint,C.c_uint64,C.c_uint];d.nf_d3d_async_skyband_poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t];d.nf_d3d_sky_input_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
 for slot,row in list(slots.items()):
  start=time.perf_counter_ns();rc=d.nf_d3d_async_skyband_poll(slot,row['capture_id'],buffers[slot],len(buffers[slot]));end=time.perf_counter_ns();assert rc in (0,3)
  if rc==3:not_ready+=1;continue
  data=buffers[slot].raw
  if row.get('coverage_only'):
   data=data[3::4]
   owner=next(r for r in rows if (r['epoch'],r['generation'],r['index'])==(row['epoch'],row['generation'],row['index']))
   owner.update(coverage_poll_begin_ns=start,coverage_poll_end_ns=end,coverage_poll_thread=threading.get_ident())
  retain(row['pixel_file'],data)
  row.update(poll_begin_ns=start,poll_end_ns=end,poll_thread=threading.get_ident());del slots[slot]
 available=next((slot for slot in range(12) if slot not in slots),None)
 if START<=count+1<START+48:
  assert available is not None
  y=[648,810,972,1134,1296,1440][(count+1-START)//8]
  d.nf_d3d_sky_stage_arm.argtypes=[C.c_uint,C.c_uint64,C.c_uint]
  assert d.nf_d3d_sky_stage_arm(available,count+1,y)==0
  world_slot=next(slot for slot in range(12) if slot not in slots and slot!=available)
  d.nf_d3d_world_stage_arm.argtypes=[C.c_uint,C.c_uint64,C.c_uint];assert d.nf_d3d_world_stage_arm(world_slot,count+1,y)==0
 result=original_prepare(self,owned,epoch,generation,index);count+=1
 if START<=count<START+48:
  available=next((slot for slot in range(12) if slot not in slots),None)
  if available is None:missed.append(dict(prepare=count,index=index));return result
  assert self.pending==(epoch,generation,index) and list(result['publication'][:3])==[epoch,generation,index]
  sequence=count-START;y=[648,810,972,1134,1296,1440][sequence//8];begin=time.perf_counter_ns();stage_info=(C.c_uint64*4)();stage_phase=C.c_double();d.nf_d3d_sky_stage_info.argtypes=[C.c_void_p,C.c_void_p];assert d.nf_d3d_sky_stage_info(stage_info,C.byref(stage_phase))==0;assert list(stage_info[:3])==[available,count,y];end=time.perf_counter_ns()
  row=dict(epoch=epoch,generation=generation,index=index,capture_id=count,sequence=sequence,y=y,x=300,width=3240,height=64,capture_begin_ns=begin,capture_end_ns=end,thread=threading.get_ident(),backend=Path(d._name).name,publication=list(result['publication']),sky_weight=stage_phase.value,context_sky_weight=owned.context.draw.weight,sky_stage_capture_ns=stage_info[3],pixel_file=str(sequence)+'.rgba',present=None)
  for input_slot in range(2):
   assert d.nf_d3d_sky_input_copy(input_slot,plane,len(plane))==0;data=plane.raw;retain(str(sequence)+'.input'+str(input_slot)+'.rgba',data)
  rows.append(row);slots[available]=row
  world_info=(C.c_uint64*4)();d.nf_d3d_world_stage_info.argtypes=[C.c_void_p];assert d.nf_d3d_world_stage_info(world_info)==0;assert list(world_info[:3])==[world_slot,count,y]
  world=dict(capture_id=count,index=index,epoch=epoch,generation=generation,y=y,pixel_file=str(sequence)+'.world.rgba',capture_ns=world_info[3],thread=threading.get_ident())
  row['world_capture']=world;slots[world_slot]=world
  final_slot=next((slot for slot in range(12) if slot not in slots),None);assert final_slot is not None
  final_begin=time.perf_counter_ns();assert d.nf_d3d_async_skyband_capture(final_slot,count,y)==0;final_end=time.perf_counter_ns()
  final=dict(capture_id=count,index=index,epoch=epoch,generation=generation,y=y,pixel_file=str(sequence)+'.final.rgba',capture_begin_ns=final_begin,capture_end_ns=final_end,thread=threading.get_ident())
  row['final_capture']=final;slots[final_slot]=final
  mask_slot=next(slot for slot in range(12) if slot not in slots)
  d.nf_d3d_async_coverage_capture.argtypes=[C.c_uint,C.c_uint64,C.c_uint]
  mask_begin=time.perf_counter_ns();assert d.nf_d3d_async_coverage_capture(mask_slot,count,y)==0;mask_end=time.perf_counter_ns()
  mask_file=str(sequence)+'.coverage.alpha'
  row.update(coverage_file=mask_file,coverage_begin_ns=mask_begin,coverage_end_ns=mask_end)
  slots[mask_slot]=dict(coverage_only=True,capture_id=count,epoch=epoch,generation=generation,index=index,pixel_file=mask_file)

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
 assert len(rows)==48 and not slots and not missed
 assert len(payloads)==288 and all('commit' in row for row in rows)
 hashes={name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()}
 for name,data in payloads.items():(folder/name).write_bytes(data)
 for row in rows:
  for part in (row,row['world_capture'],row['final_capture']):part['pixel_sha256']=hashes[part['pixel_file']]
  row['coverage_sha256']=hashes[row['coverage_file']]
  for slot in range(2):row['input'+str(slot)+'_sha256']=hashes[str(row['sequence'])+'.input'+str(slot)+'.rgba']
 (folder/'manifest.json').write_text(json.dumps(dict(capture_start=START,expected_frames=48,rows=rows,missed=missed,pending=len(slots),not_ready=not_ready,total_prepares=count,payload_bytes=payload_bytes,payload_limit=160*1024*1024,payload_files=len(payloads),writes_and_hashes_after_shutdown=True,scope='48 quadruple-stage captures; payloads held in bounded memory, hashes/files saved after shutdown. Copies and GPU diagnostic replay still perturb timing; no scanout60 certification.'),indent=2))
 print('ASYNC_SKYBAND_MANIFEST',folder/'manifest.json',flush=True)

