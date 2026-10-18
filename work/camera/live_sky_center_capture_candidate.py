"""Isolated bounded readback hook on the selected profiled native tail."""
import ctypes as C,json,time,atexit,os
from pathlib import Path
import numpy as np
import owned_present_batch_trace_install_candidate as present
selected=present.original.__globals__['ordered_tail']
assert selected.__code__.co_filename=='ordered-tail-profile-binding'
bridge=selected.__globals__['bridge'];rows=[];calls=0
commit_binding=None

def bind_commit():
 global commit_binding
 if commit_binding is not None:return
 import owned_native_transaction_worker_install_candidate as tx
 cls=tx.worker._run.__globals__['NativeSourceSession'];original_commit=cls.commit_present
 def record(self,payload,e,g,i):
  result=original_commit(self,payload,e,g,i)
  matches=[x for x in rows if x['identity']==[e,g,i]]
  if matches:
   assert len(matches)==1 and 'native_transaction' not in matches[0]
   matches[0]['native_transaction']={k:result[k] for k in ('native_result','commit','wait','stages','presentation','native_callback_count','native_batch_result','transaction_begin_ns','transaction_end_ns')}
  return result
 cls.commit_present=record;commit_binding=(cls,original_commit,record)

start=int(os.environ.get('NFSUG_SKY_CAPTURE_START','120'));limit=16
folder=Path('work/camera/prototype-runs')/('live-sky-centers-'+str(time.time_ns()));folder.mkdir()
buffer=C.create_string_buffer(3840*2160*4)
ys,xs=np.divmod(10560+np.arange(15136),240);px=(300+(xs+.5)*13.5).astype(int);py=((ys+.5)*13.5).astype(int)
Sky=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p);Hud=C.CFUNCTYPE(C.c_int,*([C.c_void_p]*4))
def hook(self,s,*args):
 global calls
 bind_commit()
 calls+=1
 if not start<=calls<start+limit:return selected(self,s,*args)
 d=self.d;identity=(C.c_uint64*3)();assert s.nf_source_packets_identity(identity)==0
 valid=(C.c_uint*2)();weights=(C.c_double*2)();assert s.nf_source_sky_info(valid,weights)==0 and list(valid)==[1,1]
 data={};errors=[];begin=time.perf_counter_ns()
 def sky(info,copy):
  try:
   rc=d.nf_d3d_source_sky_pan_batch(info,copy)
   if rc:return rc
   planes=[];s.nf_source_sky_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
   for slot in (0,1):
    q=C.create_string_buffer(153600);assert s.nf_source_sky_copy(slot,q,len(q))==0
    planes.append(np.frombuffer(q.raw,np.uint8).reshape(160,240,4)[ys,xs].copy())
   assert d.nf_d3d_read(buffer,len(buffer))==0
   data.update(lower=planes[0],upper=planes[1],stage=np.frombuffer(buffer.raw,np.uint8).reshape(2160,3840,4)[py,px].copy());return 0
  except BaseException as e:errors.append(repr(e));return -990
 def hud(*pointers):
  try:
   rc=d.nf_d3d_source_hud_batch(*pointers)
   if rc:return rc
   assert d.nf_d3d_read(buffer,len(buffer))==0
   data['final']=np.frombuffer(buffer.raw,np.uint8).reshape(2160,3840,4)[py,px].copy();return 0
  except BaseException as e:errors.append(repr(e));return -991
 sky_cb=Sky(sky);hud_cb=Hud(hud)
 class Proxy:
  def nf_ordered_render_tail_profile(self,job,size,failed,ticks):
   j=job._obj;old_sky,old_hud=j.sky,j.hud
   j.sky=C.cast(sky_cb,C.c_void_p).value;j.hud=C.cast(hud_cb,C.c_void_p).value
   try:return bridge.nf_ordered_render_tail_profile(job,size,failed,ticks)
   finally:j.sky,j.hud=old_sky,old_hud
 selected.__globals__['bridge']=Proxy()
 try:selected(self,s,*args)
 finally:selected.__globals__['bridge']=bridge
 assert not errors and set(data)=={'lower','upper','stage','final'}
 name=str(len(rows))+'.npz';np.savez(folder/name,**data)
 rows.append(dict(identity=list(identity),weight=weights[1],begin_ns=begin,end_ns=time.perf_counter_ns(),file=name,native_tail_ticks=list(self.ordered_tail_ticks)))

def finish():
 present.original.__globals__['ordered_tail']=selected
 if commit_binding is not None:
  cls,original_commit,record=commit_binding
  assert cls.commit_present is record
  cls.commit_present=original_commit
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,calls=calls,scope='Bounded native-profile sky/HUD callback readback; original seven QPC fields retained but capture overhead included. Live pixels/source identities; commit join and cadence separate.'),indent=2));print('LIVE_SKY_CENTERS',folder)
 assert len(rows)==limit,'Live sky capture hook did not execute all requested frames'
present.original.__globals__['ordered_tail']=hook
atexit.register(finish)

