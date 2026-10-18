"""Isolated visibility phase diagnostics; no selection or native semantics changes."""
import gc,threading,time
from pathlib import Path
import owned_wall_visibility_candidate as original
from owned_thread_cycles import read as cycles
records=[]
def begin(count):
 return dict(thread_id=threading.get_ident(),count=count,started_ns=time.perf_counter_ns(),stages=[],gc_before=list(gc.get_count()),gc_collections_before=[s['collections'] for s in gc.get_stats()],last_ns=time.perf_counter_ns(),last_cycles=cycles())
def mark(row,name):
 end=time.perf_counter_ns();c=cycles();row['stages'].append(dict(name=name,started_ns=row['last_ns'],completed_ns=end,thread_cycles=c-row['last_cycles']));row['last_ns']=end;row['last_cycles']=c

 if name=='output_conversion':
  row['gc_after']=list(gc.get_count());row['gc_collections_after']=[s['collections'] for s in gc.get_stats()];row['completed_ns']=end
  if len(records)<20000:records.append(row)
source=Path(original.__file__).read_text()
source=source.replace('framebuffer=calls[0][3];r=calls[0][6]','trace=begin(len(calls))\n framebuffer=calls[0][3];r=calls[0][6]')
source=source.replace('input_type,output_type=batch_types(len(calls))',"mark(trace,'domain_validation')\n input_type,output_type=batch_types(len(calls))")
source=source.replace('out=output_type();status=helper().nf_wall_visibility_batch',"out=output_type();reciprocal_buffer=table(r);native=helper()\n mark(trace,'input_packing')\n status=native.nf_wall_visibility_batch")
source=source.replace('cx,cy,table(r),len(r),out)','cx,cy,reciprocal_buffer,len(r),out)\n mark(trace,\'native_call\')')
source=source.replace('return tuple(WallVisibility(', 'result=tuple(WallVisibility(')
source=source.replace('for v in out)','for v in out)\n mark(trace,\'output_conversion\')\n return result')
namespace=dict(begin=begin,mark=mark,__file__=original.__file__)
exec(compile(source,'visibility_phase_clone','exec'),namespace)
batch=namespace['batch']
def install():original.batch=batch

