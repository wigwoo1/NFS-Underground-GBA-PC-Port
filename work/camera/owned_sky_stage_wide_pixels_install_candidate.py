"""Bounded actual pending 4K readbacks, deliberately perturbs timing."""
import ctypes as C,hashlib,json,time,threading
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession']
original_prepare=Session.prepare;original_present=Session.present
folder=Path('work/camera/prototype-runs')/('sky-stage-wide-pixels-'+str(time.time_ns()));folder.mkdir()
rows=[];pending={};count=0

def prepare(self,owned,epoch,generation,index):
 global count
 d=self.consumer.d;d.nf_d3d_sky_diag_enable.argtypes=[C.c_uint];d.nf_d3d_sky_diag_copy.argtypes=[C.c_void_p,C.c_size_t]
 assert d.nf_d3d_sky_diag_enable(int(120<=count+1<152))==0
 result=original_prepare(self,owned,epoch,generation,index);count+=1
 if 120<=count<152:
  assert self.pending==(epoch,generation,index) and list(result['publication'][:3])==[epoch,generation,index]
  begin=time.perf_counter_ns();sky_buffer=C.create_string_buffer(640*16*4);world_buffer=C.create_string_buffer(640*16*4)
  assert self.consumer.d.nf_d3d_read_region(1600,600,640,16,sky_buffer,len(sky_buffer))==0
  assert self.consumer.d.nf_d3d_read_region(1600,1200,640,16,world_buffer,len(world_buffer))==0
  native_read_end=time.perf_counter_ns();sky=sky_buffer.raw;world=world_buffer.raw
  name=str(len(rows));(folder/(name+'.sky.rgba')).write_bytes(sky);(folder/(name+'.world.rgba')).write_bytes(world)
  stage=C.create_string_buffer(3840*16*4);assert d.nf_d3d_sky_diag_copy(stage,len(stage))==0;stage_bytes=stage.raw;(folder/(name+".sky-stage.rgba")).write_bytes(stage_bytes)
  draw=owned.context.draw
  row=dict(sky_stage_width=3840,sky_stage_x=0,sky_stage_sha256=hashlib.sha256(stage_bytes).hexdigest(),sky_stage_file=name+".sky-stage.rgba",epoch=epoch,generation=generation,index=index,publication=list(result['publication']),thread=threading.get_ident(),begin_ns=begin,end_ns=time.perf_counter_ns(),width=3840,height=2160,native_read_end_ns=native_read_end,region_width=640,region_height=16,region_x=1600,sky_sha256=hashlib.sha256(sky).hexdigest(),world_sha256=hashlib.sha256(world).hexdigest(),sky_file=name+'.sky.rgba',world_file=name+'.world.rgba',sky_weight=draw.weight,sky_lower=hashlib.sha256(C.string_at(draw.lower,draw.skycount)).hexdigest(),sky_upper=hashlib.sha256(C.string_at(draw.upper,draw.skycount)).hexdigest(),present=None)
  rows.append(row);pending[epoch,generation,index]=row
 return result

def present(self,epoch,generation,index):
 result=original_present(self,epoch,generation,index);row=pending.pop((epoch,generation,index),None)
 if row is not None:row['present']=dict(status=result['status'],thread=threading.get_ident(),end_ns=time.perf_counter_ns())
 return result
Session.prepare=prepare;Session.present=present
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
original_run=NativeSourceCommitAdapter.run
def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,**kwargs):
 result=original_run(self,owned,epoch,generation,older,newer,index,alpha,deadline,**kwargs)
 row=next((x for x in rows if (x['epoch'],x['generation'],x['index'])==(epoch,generation,index)),None)
 if row is not None:row.update(source_older=older,source_newer=newer,alpha=alpha,native_result=result['native_result'],commit=result['commit'])
 return result
NativeSourceCommitAdapter.run=run

def save():
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,total_prepares=count,pending=len(pending),scope='32 bounded pending4Kdraw regionreadbacks 640x16 at x1600/y600 and1200, explicit sourcepair/presentation identities; bands mayincludeoverlap. No skyisolation/fullfidelity/scanout/cadence proof; readbackperturbs timing.'),indent=2));print('ORDERED_TAIL_PIXEL_MANIFEST',folder/'manifest.json',flush=True)
