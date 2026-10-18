"""Bounded call-site counts for transient ctypes string buffers; diagnostic only."""
import ctypes as C,runpy,sys,json,collections
from pathlib import Path
from live_owned_gpu_worker import LiveOwnedGPUWorker
original_buffer=C.create_string_buffer;original_submit=LiveOwnedGPUWorker.submit
count=0;active=False;saved=False;calls=collections.Counter();dropped=0

def buffer(*args,**kwargs):
 global dropped
 value=original_buffer(*args,**kwargs)
 if active:
  caller=sys._getframe(1);key=(Path(caller.f_code.co_filename).name,caller.f_code.co_name,caller.f_lineno,C.sizeof(value));caller=None
  if key in calls or len(calls)<256:calls[key]+=1
  else:dropped+=1
 return value

def submit(self,*args,**kwargs):
 global count,active,saved
 count+=1
 if count==80:active=True
 if count==100:
  active=False;saved=True
  out=dict(result='BOUNDED_BUFFER_CALLSITE_ATTRIBUTION',submissions=[80,100],unique_sites=len(calls),dropped_sites=dropped,rows=[dict(file=k[0],function=k[1],line=k[2],bytes=k[3],calls=v) for k,v in calls.most_common()],scope='ctypes.create_string_buffer call sites over20 scene submissions in all same-process threads. Temporary caller frames released immediately; no buffer retention. Stack/Counter instrumentation perturbs timing; no speed or cadence qualification. Other allocation APIs not covered.')
  Path('work/camera/prototype-runs/buffer-callsites-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
 return original_submit(self,*args,**kwargs)
C.create_string_buffer=buffer;LiveOwnedGPUWorker.submit=submit
try:
 runpy.run_path('work/camera/run_native_visibility_thread_library_candidate.py',run_name='__main__');assert saved
finally:
 active=False;C.create_string_buffer=original_buffer;LiveOwnedGPUWorker.submit=original_submit
