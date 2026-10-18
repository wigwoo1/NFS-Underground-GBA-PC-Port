import os
capture_begin=int(os.environ.get("NF_SKY_CAPTURE_BEGIN","120"))
assert 1<=capture_begin<=2000
"""Bounded synchronous pixel diagnostic; never performance qualification."""
import ctypes as C,time,json,threading
from pathlib import Path
import numpy as np
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
folder=Path("work/camera/prototype-runs")/("linear-sky-pixels-"+str(time.time_ns()));folder.mkdir()
rows=[];count=0
original_render=OwnedD3DConsumer.render
def render(self,s,*args,**kwargs):
 global count
 result=original_render(self,s,*args,**kwargs);count+=1
 if capture_begin<=count<capture_begin+16:
  publication=(C.c_uint64*3)();s.nf_source_packets_identity.argtypes=[C.c_void_p];assert s.nf_source_packets_identity(publication)==0
  enabled=(C.c_uint*2)();weights=(C.c_double*2)()
  s.nf_source_sky_info.argtypes=[C.c_void_p,C.c_void_p];assert s.nf_source_sky_info(enabled,weights)==0
  assert list(enabled)==[1,1]
  planes=[]
  s.nf_source_sky_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
  for slot in range(2):
   plane=C.create_string_buffer(153600);assert s.nf_source_sky_copy(slot,plane,len(plane))==0
   planes.append(np.frombuffer(plane.raw,np.uint8).reshape(160,240,4).copy())
  buf=C.create_string_buffer(3840*2160*4);begin=time.perf_counter_ns()
  assert self.d.nf_d3d_read(buf,len(buf))==0;end=time.perf_counter_ns()
  band=np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4)[594:1458:27,300:3540].copy()
  file=folder/(str(len(rows))+".npz");np.savez_compressed(file,actual=band,lower=planes[0],upper=planes[1])
  rows.append(dict(identity=list(publication[:3]),phase=weights[1],file=str(file),thread=threading.get_ident(),read_begin_ns=begin,read_end_ns=end,backend=self.d._name,commit=None))
 return result
OwnedD3DConsumer.render=render
original_run=NativeSourceCommitAdapter.run
def run(self,owned,e,g,older,newer,index,alpha,deadline,**kwargs):
 result=original_run(self,owned,e,g,older,newer,index,alpha,deadline,**kwargs)
 row=next((x for x in rows if x["identity"]==[e,g,index]),None)
 if row is not None:row.update(commit=result["commit"],native_result=result["native_result"],alpha=alpha,older=older,newer=newer)
 return result
NativeSourceCommitAdapter.run=run
def save():
 path=folder/"manifest.json";path.write_text(json.dumps(dict(rows=rows,scope="Synchronous diagnostic readbacks perturb timing; pixels and sample identities only, no scanout or performance claim."),indent=2));print("LINEAR_SKY_PIXELS",path)
