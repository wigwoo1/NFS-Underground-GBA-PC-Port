import ctypes as C,json,threading
from pathlib import Path
import numpy as np
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-sky-pan-candidate.dll').resolve()));P=C.c_void_p
for n,a in [('nf_d3d_clear',[P]),('nf_d3d_texture',[C.c_uint,C.c_uint,C.c_uint,P,C.c_size_t]),('nf_d3d_read',[P,C.c_size_t]),('nf_d3d_sky_pan',[C.c_float]),('nf_d3d_sky_quad',[C.c_uint,C.c_float])]:getattr(d,n).argtypes=a
assert d.nf_d3d_open()==0
buf=C.create_string_buffer(3840*2160*4)
def read():
 assert d.nf_d3d_read(buf,len(buf))==0
 return np.frombuffer(buf.raw,np.uint8).reshape(2160,3840,4).copy()
def clear():assert d.nf_d3d_clear((C.c_float*4)(0,0,0,1))==0
try:
 assert d.nf_d3d_sky_pan(.5)==1
 for layer,edge in enumerate((120,119)):
  a=np.zeros((160,240,4),np.uint8);a[44:107,edge:]=[255,0,0,255];a[107,:16]=[0,255,0,255]
  assert d.nf_d3d_texture(1001+layer,240,160,a.ctypes.data,a.nbytes)==0
 planes=[]
 for edge in (120,119):
  a=np.zeros((160,240,4),np.uint8);a[44:107,edge:]=[255,0,0,255];a[107,:16]=[0,255,0,255];planes.append(a)
 phase_value=[0.0]
 Info=C.CFUNCTYPE(C.c_int,C.POINTER(C.c_uint),C.POINTER(C.c_double));Copy=C.CFUNCTYPE(C.c_int,C.c_uint,P,C.c_size_t)
 @Info
 def info(enabled,weights):
  enabled[0]=enabled[1]=1;weights[0]=1;weights[1]=phase_value[0];return 0
 @Copy
 def copy(layer,target,size):
  if size!=153600:return 1
  C.memmove(target,planes[layer].ctypes.data,size);return 0
 d.nf_d3d_source_sky_pan_batch.argtypes=[Info,Copy]
 enabled_state=[1,1];failure=[-1];calls=[];info_status=[0]
 @Info
 def guarded_info(enabled,weights):
  for i in range(2):enabled[i]=enabled_state[i];weights[i]=1 if i==0 else phase_value[0]
  return info_status[0]
 @Copy
 def guarded_copy(layer,target,size):
  calls.append(layer)
  if failure[0]==layer:return 1
  C.memmove(target,planes[layer].ctypes.data,size);return 0
 def invoke():return d.nf_d3d_source_sky_pan_batch(guarded_info,guarded_copy)
 clear();assert d.nf_d3d_sky_pan(0)==0;lower=read()
 phase_value[0]=.5
 for flags in ([0,0],[0,1],[2,1]):
  enabled_state[:]=flags;calls.clear();clear();before=read();status=invoke();assert status==(0 if flags==[0,0] else 1);assert not calls and np.array_equal(before,read())
 enabled_state[:]=[1,0];calls.clear();clear();assert invoke()==0;assert calls==[0] and np.array_equal(lower,read()),'Missing upper must use corrected lower phase, never stale upper'
 enabled_state[:]=[1,1]
 for failed_layer in (0,1):
  failure[0]=failed_layer;clear();before=read();assert invoke()==1;assert np.array_equal(before,read()),'Failed source copy drew partial sky'
 failure[0]=-1
 for bad in (-1,2,float('nan')):
  phase_value[0]=bad;calls.clear();assert invoke()==1 and not calls
 phase_value[0]=.5;info_status[0]=1;calls.clear();assert invoke()==1 and not calls;info_status[0]=0
 clear();assert invoke()==0;recovered=read();clear();assert d.nf_d3d_sky_pan(.5)==0;assert np.array_equal(recovered,read())
 errors=[];t=threading.Thread(target=lambda:errors.append(invoke()));t.start();t.join();assert errors==[1]
finally:assert d.nf_d3d_close()==0
out=dict(result='PASS_SKY_SOURCE_FAILURE_RECOVERY',disabled_no_draw=True,orphan_upper_rejected=True,missing_upper_precise_lower=True,copy_failure_no_partial_draw=True,invalid_phase_no_copy=True,info_failure_no_copy=True,recovery_pixel_parity=True,wrong_owner_rejected=True,scope='Actual GPU callback guards and recovery with synthetic textures, not live ROM fidelity or physical60fps.')
(p/'prototype-runs/sky-source-recovery-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
