"""Bounded immutable slow-draw inputs; files written only after worker shutdown."""
import json,struct,time,hashlib,math
from pathlib import Path
class SlowHudCapture:
 def __init__(self,limit=3,budget=32*1024*1024):self.limit=limit;self.budget=budget;self.records=[];self.bytes=0;self.identities=set();self.rejected=0
 def add(self,metadata,value,sky,profile):
  frame,camera,models,bounds,detail=value
  if len(frame)<40:raise ValueError('Truncated capture frame')
  h=struct.unpack_from('<6I2Q',frame);identity=(h[6],h[1])
  if h[0]!=0x3346474e or h[7]!=h[1]*280896 or 40+sum(h[2:6])!=len(frame):raise ValueError('Capture frame layout/identity')
  if identity in self.identities:return False
  if len(self.records)>=self.limit:self.rejected+=1;return False
  n=detail['geometry_records']
  if len(camera)!=12 or len(models)!=12*n or len(bounds)!=4*n or len(sky.lower)!=15136 or len(sky.upper)!=15136 or not math.isfinite(sky.weight):raise ValueError('Capture owner sizes')
  started=time.perf_counter_ns();cpu=time.thread_time_ns()
  payload=dict(frame=frame,camera=bytes(camera),models=bytes(models),bounds=bytes(bounds),lower=bytes(sky.lower),upper=bytes(sky.upper))
  size=sum(map(len,payload.values()))
  if self.bytes+size>self.budget:self.rejected+=1;return False
  meta=dict(metadata,frame_refresh=h[1],epoch=h[6],geometry_records=n,sky_weight=sky.weight,draw_profile=list(profile),capture_copy_ns=time.perf_counter_ns()-started,capture_copy_thread_cpu_ns=time.thread_time_ns()-cpu)
  self.records.append((meta,payload));self.identities.add(identity);self.bytes+=size;return True
 def save(self,folder):
  folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);rows=[]
  for i,(meta,payload) in enumerate(self.records):
   target=folder/str(i);target.mkdir();files={}
   for name,data in payload.items():
    p=target/(name+'.bin');p.write_bytes(data);files[name]=dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   rows.append(dict(meta,files=files))
  result=dict(scope='Immutable exact sampled frame/pose/clips/sky from slow draw; capture overhead invalidates cadence performance comparisons.',records=rows,retained_bytes=self.bytes,rejected=self.rejected)
  p=folder/'captures.json';p.write_text(json.dumps(result,indent=2));self.records.clear();self.identities.clear();self.bytes=0;return str(p)
