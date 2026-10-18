"""Bounded owner-thread pre-world and completed-world sky pixel diagnostic."""
import ctypes as C,time,json,threading
from pathlib import Path
import numpy as np
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
folder=Path('work/camera/prototype-runs')/('progressive-sky-stage-'+str(time.time_ns()));folder.mkdir()
rows=[];calls=0;original=OwnedD3DConsumer.render
class SkyCaptureProxy:
 def __init__(self,d,source):self.d=d;self.source=source;self.row=None;self.stage=None
 def __getattr__(self,name):
  function=getattr(self.d,name)
  if name!='nf_d3d_source_sky_pan_batch':return function
  def draw(*args):
   result=function(*args)
   assert result==0
   self.source.nf_source_packets_identity.argtypes=[C.c_void_p]
   self.source.nf_source_sky_info.argtypes=[C.c_void_p,C.c_void_p]
   self.source.nf_source_sky_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
   identity=(C.c_uint64*3)();assert self.source.nf_source_packets_identity(identity)==0
   enabled=(C.c_uint*2)();weights=(C.c_double*2)();assert self.source.nf_source_sky_info(enabled,weights)==0
   assert list(enabled)==[1,1]
   planes=[]
   for slot in range(2):
    plane=C.create_string_buffer(153600);assert self.source.nf_source_sky_copy(slot,plane,len(plane))==0
    planes.append(np.frombuffer(plane.raw,np.uint8).reshape(160,240,4).copy())
   buf=C.create_string_buffer(3840*2160*4);begin=time.perf_counter_ns();assert self.d.nf_d3d_read(buf,len(buf))==0;end=time.perf_counter_ns()
   self.stage=np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4)[594:1458:27,300:3540].copy()
   self.planes=planes;self.row=dict(identity=list(identity),phase=weights[1],thread=threading.get_ident(),sky_read_begin_ns=begin,sky_read_end_ns=end,backend=self.d._name,commit=None)
   return result
  def guarded(*args):
   try:return draw(*args)
   except BaseException as error:self.error=repr(error);return 99
  self.callback=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p)(guarded)
  return self.callback

def render(self,source,*args,**kwargs):
 global calls
 calls+=1
 if not 120<=calls<136:return original(self,source,*args,**kwargs)
 native=self.d;proxy=SkyCaptureProxy(native,source);self.d=proxy
 try:result=original(self,source,*args,**kwargs)
 finally:self.d=native
 assert proxy.row is not None,'Sky draw interception absent'
 buf=C.create_string_buffer(3840*2160*4);begin=time.perf_counter_ns();assert native.nf_d3d_read(buf,len(buf))==0;end=time.perf_counter_ns()
 full=np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4)[594:1458:27,300:3540].copy()
 file=folder/(str(len(rows))+'.npz');np.savez_compressed(file,sky=proxy.stage,actual=full,lower=proxy.planes[0],upper=proxy.planes[1])
 proxy.row.update(file=str(file),full_read_begin_ns=begin,full_read_end_ns=end);rows.append(proxy.row)
 return result
OwnedD3DConsumer.render=render
original_run=NativeSourceCommitAdapter.run

def run(self,owned,e,g,older,newer,index,alpha,deadline,**kwargs):
 result=original_run(self,owned,e,g,older,newer,index,alpha,deadline,**kwargs)
 row=next((r for r in rows if r['identity']==[e,g,index]),None)
 if row is not None:row.update(commit=result['commit'],native_result=result['native_result'],older=older,newer=newer,alpha=alpha)
 return result
NativeSourceCommitAdapter.run=run

def save():
 path=folder/'manifest.json';path.write_text(json.dumps(dict(rows=rows,scope='Pre-world sky and completed fullscene owner-thread readbacks; perturbs timing; no performance qualification.'),indent=2));print('PROGRESSIVE_SKY_STAGE',path)
