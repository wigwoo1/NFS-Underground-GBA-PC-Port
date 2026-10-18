"""Isolated per-producer-stage CPU/cycle and native capture boundary diagnostics."""
import runpy,sys,re
from pathlib import Path
original_read=Path.read_text
target=Path('work/camera/run_owned_native_prototype.py').resolve()
def read(path,*args,**kwargs):
 source=original_read(path,*args,**kwargs)
 if path.resolve()!=target:return source
 needle='size=C.c_size_t();frame_read_boundaries=[]'
 assert source.count(needle)==1
 source=source.replace(needle,'''size=C.c_size_t();frame_read_boundaries=[]
  stage_cpu={};stage_cycles={};cpu_begin=time.thread_time_ns();cycle_begin=thread_cycles()
  def finish_stage(name):
   nonlocal stage_begin,cpu_begin,cycle_begin
   wall_end=time.perf_counter_ns();cpu_end=time.thread_time_ns();cycle_end=thread_cycles()
   stage_times[name]=wall_end-stage_begin;stage_cpu[name]=cpu_end-cpu_begin;stage_cycles[name]=cycle_end-cycle_begin
   stage_begin=time.perf_counter_ns();cpu_begin=time.thread_time_ns();cycle_begin=thread_cycles()''')
 pattern=r"stage_times\['([^']+)'\]=time.perf_counter_ns\(\)-stage_begin;stage_begin=time.perf_counter_ns\(\)"
 source,n=re.subn(pattern,lambda m:"finish_stage("+repr(m[1])+")",source);assert n==7
 needle="stage_times['worker_submit_ns']=time.perf_counter_ns()-stage_begin"
 assert source.count(needle)==1;source=source.replace(needle,"finish_stage('worker_submit_ns')")
 source=source.replace('stages=stage_times,frame_read_boundaries=','stages=stage_times,stage_thread_cpu_ns=stage_cpu,stage_thread_cycles=stage_cycles,frame_read_boundaries=')
 return source
Path.read_text=read
if '--native-capture-boundary' not in sys.argv:sys.argv.append('--native-capture-boundary')
runpy.run_path('work/camera/run_source_array_copy_candidate.py',run_name='__main__')
