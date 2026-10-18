import ctypes as C,hashlib,json,time,threading
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession']
original_prepare=Session.prepare
original_present=Session.present
folder=Path('work/camera/prototype-runs')/('current-backend-sky-readback-'+str(time.time_ns()))
folder.mkdir()
rows=[]
count=0
pending={}
def prepare(self,owned,epoch,generation,index):
 global count
 d=self.consumer.d;d.nf_d3d_current_sky_stage_enable.argtypes=[C.c_uint]
 assert d.nf_d3d_current_sky_stage_enable(int(120<=count+1<152))==0
 result=original_prepare(self,owned,epoch,generation,index)
 count+=1
 if 120<=count<152:
  assert self.pending==(epoch,generation,index)
  assert list(result['publication'][:3])==[epoch,generation,index]
  begin=time.perf_counter_ns()
  rgba=C.create_string_buffer(3840*16*4)
  d=self.consumer.d;d.nf_d3d_read_region.argtypes=[C.c_uint]*4+[C.c_void_p,C.c_size_t]
  assert d.nf_d3d_read_region(0,648,3840,16,rgba,len(rgba))==0
  data=strip=rgba.raw
  stage=C.create_string_buffer(3840*16*4);d.nf_d3d_current_sky_stage_copy.argtypes=[C.c_void_p,C.c_size_t]
  assert d.nf_d3d_current_sky_stage_copy(stage,len(stage))==0
  (folder/(str(len(rows))+'.stage.rgba')).write_bytes(stage.raw)
  d.nf_d3d_sky_input_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
  for slot in range(2):
   plane=C.create_string_buffer(240*160*4);assert d.nf_d3d_sky_input_copy(slot,plane,len(plane))==0
   (folder/(str(len(rows))+'.input'+str(slot)+'.rgba')).write_bytes(plane.raw)
  name=str(len(rows))+'.skyband16.rgba'
  (folder/name).write_bytes(strip)
  draw=owned.context.draw
  row=dict(epoch=epoch,generation=generation,index=index,prepare_number=count,publication=list(result['publication']),thread=threading.get_ident(),read_begin_ns=begin,read_end_ns=time.perf_counter_ns(),width=3840,height=2160,strip_y=648,strip_height=16,strip_file=name,backend=Path(self.consumer.d._name).name,rgba_sha256=hashlib.sha256(data).hexdigest(),strip_sha256=hashlib.sha256(strip).hexdigest(),sky_weight=draw.weight,sky_lower_sha256=hashlib.sha256(C.string_at(draw.lower,draw.skycount)).hexdigest(),sky_upper_sha256=hashlib.sha256(C.string_at(draw.upper,draw.skycount)).hexdigest(),present=None)
  rows.append(row)
  pending[epoch,generation,index]=row
 return result
def present(self,epoch,generation,index):
 result=original_present(self,epoch,generation,index)
 row=pending.pop((epoch,generation,index),None)
 if row is not None:row['present']=dict(status=result['status'],completed_ns=time.perf_counter_ns(),thread=threading.get_ident())
 return result
Session.prepare=prepare
Session.present=present
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
original_run=NativeSourceCommitAdapter.run
def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,**kwargs):
 result=original_run(self,owned,epoch,generation,older,newer,index,alpha,deadline,**kwargs)
 for row in rows:
  if (row['epoch'],row['generation'],row['index'])==(epoch,generation,index):
   assert 'commit' not in row
   row.update(source_older=older,source_newer=newer,alpha=alpha,deadline_ns=deadline,native_result=result['native_result'],commit=result['commit'])
 return result
NativeSourceCommitAdapter.run=run
def save():
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,total_prepares=count,pending=len(pending),scope='32 bounded current-backend final y594:658 readbacks; foreground/HUD overlap possible, no sky-exclusive/cadence proof.'),indent=2))
 print('CURRENT_SKY_MANIFEST',folder/'manifest.json',flush=True)
