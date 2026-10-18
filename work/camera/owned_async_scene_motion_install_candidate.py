"""Bounded async scene bands: GPU owner polls; file IO occurs after shutdown."""
import ctypes as C,time,json,threading,os
from pathlib import Path
from owned_uncovered_window_candidate import OwnedD3DConsumer
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
folder=Path('work/camera/prototype-runs')/('async-scene-motion-'+str(time.time_ns()));folder.mkdir()
windows=tuple(int(x) for x in os.environ.get('NF_SCENE_CAPTURE_WINDOWS','300').split(','));assert 1<=len(windows)<=3 and all(1<=x<=7000 for x in windows) and all(b-a>=16 for a,b in zip(windows,windows[1:]))
rows=[];owners={};slots={};pixels={};count=0;not_ready=0;missed=[]
buffers=[C.create_string_buffer(3240*64*4) for _ in range(9)]
original_render=OwnedD3DConsumer.render

def render(self,s,*args,**kwargs):
 global count,not_ready
 d=self.d
 d.nf_d3d_async_skyband_capture.argtypes=[C.c_uint,C.c_uint64,C.c_uint]
 d.nf_d3d_async_skyband_poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t]
 for slot,row in list(slots.items()):
  begin=time.perf_counter_ns();rc=d.nf_d3d_async_skyband_poll(slot,row['capture_id'],buffers[slot],len(buffers[slot]));end=time.perf_counter_ns()
  assert rc in (0,3),rc
  if rc==3:not_ready+=1;continue
  pixels[row['sequence']]=buffers[slot].raw
  row.update(poll_begin_ns=begin,poll_end_ns=end,poll_thread=threading.get_ident());del slots[slot]
 result=original_render(self,s,*args,**kwargs);count+=1
 if any(start<=count<start+16 for start in windows):
  identity=(C.c_uint64*3)();s.nf_source_packets_identity.argtypes=[C.c_void_p];assert s.nf_source_packets_identity(identity)==0
  for y in (216,1080,1944):
   slot=next((i for i in range(9) if i not in slots),None)
   if slot is None:missed.append(dict(identity=list(identity),y=y));continue
   sequence=len(rows);capture_id=sequence+1;begin=time.perf_counter_ns();assert d.nf_d3d_async_skyband_capture(slot,capture_id,y)==0;end=time.perf_counter_ns()
   row=dict(identity=list(identity),capture_id=capture_id,sequence=sequence,y=y,width=3240,height=64,capture_begin_ns=begin,capture_end_ns=end,thread=threading.get_ident(),backend=d._name,commit=None)
   rows.append(row);owners.setdefault(tuple(identity),[]).append(row);slots[slot]=row
 return result
OwnedD3DConsumer.render=render
original_run=NativeSourceCommitAdapter.run

def run(self,owned,e,g,older,newer,index,alpha,deadline,**kwargs):
 result=original_run(self,owned,e,g,older,newer,index,alpha,deadline,**kwargs)
 for row in rows:
  if row['identity']==[e,g,index]:row.update(commit=result['commit'],native_result=result['native_result'],alpha=alpha,older=older,newer=newer)
 return result
NativeSourceCommitAdapter.run=run

def save():
 import hashlib
 for row in rows:
  if row['sequence'] in pixels:
   data=pixels[row['sequence']];file=folder/(str(row['sequence'])+'.rgba');file.write_bytes(data);row.update(file=str(file),sha256=hashlib.sha256(data).hexdigest())
 out=dict(windows=list(windows),expected_captures=48*len(windows),rows=rows,missed=missed,pending=len(slots),not_ready=not_ready,scope='Up to144 attempted asynchronous64-row captures in3 fixedscene bands; bounded120MB hostpayload. FileIO/hash after shutdown, GPU poll nonblocking. Copies still perturb timing; no scanout/semanticlayer proof.')
 (folder/'manifest.json').write_text(json.dumps(out,indent=2));print('ASYNC_SCENE_MOTION',folder/'manifest.json',flush=True)
