"""Bounded live readback diagnostic; deliberately perturbs pacing."""
import ctypes as C,hashlib,json,runpy,time,threading
from pathlib import Path
import run_native_async_handoff_candidate
import owned_hud_cache_lease_worker_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_renderer_fixed_types_install_candidate
import owned_hud_prefetch_d3d_profile_install_candidate
import owned_packet_profile_install_candidate
import owned_d3d_call_profile_install_candidate
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession']
original_prepare=Session.prepare
original_present=Session.present
folder=Path('work/camera/prototype-runs')/('live-sky-stage-readback-'+str(time.time_ns()))
folder.mkdir()
rows=[]
count=0
pending={}
class SkyStageReadback:
 def __init__(self,session):self.session=session;self.base=session.consumer.d;self.capture=None
 def __getattr__(self,name):return getattr(self.base,name)
 def nf_d3d_source_sky_pan_batch(self,*args):
  result=self.base.nf_d3d_source_sky_pan_batch(*args)
  assert result==0
  rgba=C.create_string_buffer(3840*2160*4)
  assert self.base.nf_d3d_read(rgba,len(rgba))==0
  strip=rgba.raw[3840*600*4:3840*664*4]
  source=self.session.source;n=source.nf_source_backdrop_count();assert n in (0,160)
  backdrop=C.create_string_buffer(640)
  if n:
   source.nf_source_backdrop_copy.argtypes=[C.c_void_p,C.c_size_t]
   assert source.nf_source_backdrop_copy(backdrop,640)==0
  self.capture=(strip,hashlib.sha256(backdrop.raw if n else b'').hexdigest())
  return result
def prepare(self,owned,epoch,generation,index):
 global count
 target=120<=count+1<152
 base=self.consumer.d
 proxy=SkyStageReadback(self) if target else None
 if target:self.consumer.d=proxy
 try:result=original_prepare(self,owned,epoch,generation,index)
 finally:self.consumer.d=base
 count+=1
 if 120<=count<152:
  assert self.pending==(epoch,generation,index)
  assert list(result['publication'][:3])==[epoch,generation,index]
  begin=time.perf_counter_ns()
  rgba=C.create_string_buffer(3840*2160*4)
  self.consumer.d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
  assert self.consumer.d.nf_d3d_read(rgba,len(rgba))==0
  data=rgba.raw
  strip=data[3840*600*4:3840*664*4]
  name=str(len(rows))+'.skyband64.rgba'
  (folder/name).write_bytes(strip)
  draw=owned.context.draw
  row=dict(epoch=epoch,generation=generation,index=index,prepare_number=count,publication=list(result['publication']),thread=threading.get_ident(),read_begin_ns=begin,read_end_ns=time.perf_counter_ns(),width=3840,height=2160,strip_height=64,strip_y=600,strip_file=name,rgba_sha256=hashlib.sha256(data).hexdigest(),strip_sha256=hashlib.sha256(strip).hexdigest(),sky_weight=draw.weight,sky_lower_sha256=hashlib.sha256(C.string_at(draw.lower,draw.skycount)).hexdigest(),sky_upper_sha256=hashlib.sha256(C.string_at(draw.upper,draw.skycount)).hexdigest(),present=None)
  assert proxy.capture is not None
  sky_strip,backdrop_hash=proxy.capture
  sky_name=str(len(rows))+'.sky-stage-skyband64.rgba'
  (folder/sky_name).write_bytes(sky_strip)
  row.update(sky_stage_strip_file=sky_name,sky_stage_strip_sha256=hashlib.sha256(sky_strip).hexdigest(),backdrop_sha256=backdrop_hash)
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
try:
 runpy.run_module('run_native_async_handoff_candidate',run_name='__main__')
finally:
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,total_prepares=count,scope='Actual 4K pending draw readback on native renderer thread before presentation, bounded32. Top64 includes any world/HUD overlap; pixel changes do not isolate sky. Readback perturbs pacing; no physical scanout proof.'),indent=2))
 print('LIVE_SKY_READBACK_MANIFEST',folder/'manifest.json',flush=True)
