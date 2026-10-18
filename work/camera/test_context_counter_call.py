"""Counter-only FFI parity and competing Python-thread latency; no gameplay claim."""
import ctypes as C,json,threading,time,statistics,sys
from pathlib import Path
p=Path('work/camera');gpu=C.CDLL(str((p/'owned-sky-gpu.dll').resolve()))
gpu.nf_owned_gpu_contexts.restype=C.c_uint
held=C.PYFUNCTYPE(C.c_uint)(C.cast(gpu.nf_owned_gpu_contexts,C.c_void_p).value)
assert held()==gpu.nf_owned_gpu_contexts()
# No GL work or renderer ownership mutation: this export reads one unsigned.
stop=threading.Event();started=threading.Event()
def competitor():
 started.set();value=0
 while not stop.is_set():
  for n in range(1000):value=(value+n)&65535
thread=threading.Thread(target=competitor);old=sys.getswitchinterval();sys.setswitchinterval(.001);thread.start();assert started.wait(5)
rows=[]
try:
 for trial in range(6):
  name,fn=('cdll',gpu.nf_owned_gpu_contexts) if trial%2==0 else ('held_gil',held)
  values=[]
  for repeat in range(200):
   begin=time.perf_counter_ns();result=fn();end=time.perf_counter_ns();assert result==0;values.append((end-begin)/1e6)
  rows.append(dict(variant=name,trial=trial,median_ms=statistics.median(values),max_ms=max(values),over_1ms=sum(v>1 for v in values)))
finally:stop.set();thread.join(5);sys.setswitchinterval(old)
assert not thread.is_alive()
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-context-counter-call-20261006');(out/'counter-test.json').write_text(json.dumps(dict(result='PASS',queries=1200,trials=rows,scope='Exact pure native counter with competing Python worker; no GPU draw, window, scanout or live performance certification'),indent=2));print(rows)
