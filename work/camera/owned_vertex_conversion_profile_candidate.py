"""Diagnostic-only NumPy vertex conversion clocks, unchanged call/output."""
import time,numpy as np,threading,atexit,json
from collections import deque
from pathlib import Path
from owned_thread_cycles import read
original_copyto=np.copyto
rows=deque(maxlen=1024)
def copyto(dst,src,*args,**kwargs):
 if getattr(dst,'ndim',0)!=2 or dst.shape[1]!=10 or dst.dtype!=np.float32 or getattr(src,'dtype',None)!=np.float64:return original_copyto(dst,src,*args,**kwargs)
 c0=read();t0=time.perf_counter_ns();result=original_copyto(dst,src,*args,**kwargs);t1=time.perf_counter_ns();c1=read()
 rows.append(dict(begin_ns=t0,end_ns=t1,cycles=c1-c0,vertices=dst.shape[0],input_bytes=src.nbytes,output_bytes=dst.nbytes,thread=threading.get_ident()))
 return result
np.copyto=copyto
def save():
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/vertex-conversion-profile-20261010/conversions.json').write_text(json.dumps(list(rows),indent=2))
atexit.register(save)
