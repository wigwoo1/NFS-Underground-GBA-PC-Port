"""Explicit owner-thread Python-call timing; wall durations include scheduling waits."""
import sys,threading,time,json
class ThreadProfile:
 def __init__(self):self.owner=None;self.active={};self.rows={};self.foreign_events=0
 def event(self,frame,event,arg):
  if threading.get_ident()!=self.owner:self.foreign_events+=1;return
  if event not in ('call','return'):return
  now=time.perf_counter_ns();cpu_now=time.thread_time_ns()
  if event=='call':self.active[id(frame)]=(frame.f_code,now,cpu_now)
  else:
   saved=self.active.pop(id(frame),None)
   if saved is None:return
   code,begin,cpu_begin=saved;key=(code.co_filename,code.co_firstlineno,code.co_name)
   row=self.rows.setdefault(key,[0,0,0]);row[0]+=1;row[1]+=now-begin;row[2]+=cpu_now-cpu_begin
 def run(self,function,*args,**kwargs):
  self.owner=threading.get_ident();previous=sys.getprofile()
  try:
   sys.setprofile(self.event)
   return function(*args,**kwargs)
  finally:sys.setprofile(previous);self.active.clear()
 def save(self,path):
  rows=[dict(file=k[0],line=k[1],function=k[2],calls=v[0],inclusive_wall_ns=v[1],inclusive_thread_cpu_ns=v[2],wall_minus_coarse_cpu_ns=v[1]-v[2]) for k,v in self.rows.items()]
  path.write_text(json.dumps(dict(owner_thread=self.owner,foreign_events_excluded=self.foreign_events,scope='Owner-thread Python calls; inclusive wall and coarse Windows thread CPU include profiler overhead; residual may be negative from quantization; excludes separate C-call attribution',rows=sorted(rows,key=lambda x:x['inclusive_wall_ns'],reverse=True)),indent=2))
