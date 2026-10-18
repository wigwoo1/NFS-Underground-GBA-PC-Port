"""Bounded slow-call visibility trace, private fixed scratch per thread, no GC snapshots."""
import threading,time
import owned_wall_visibility_phases as template
from owned_thread_cycles import read as cycles
local=threading.local();records=[];completed=0;dropped=0
threshold_ns=1000000
names=('domain_validation','input_packing','native_call','output_conversion')
def begin(count):
 start=time.perf_counter_ns()
 if not hasattr(local,'scratch'):local.scratch=[0]*13
 row=local.scratch;row[0]=count;row[1]=start;row[2]=time.perf_counter_ns();row[3]=cycles()
 return row
def mark(row,name):
 global completed,dropped
 index=names.index(name);row[4+index*2]=time.perf_counter_ns();row[5+index*2]=cycles()
 if index==3:
  completed+=1
  if row[10]-row[1]>=threshold_ns:
   if len(records)<1000:records.append((threading.get_ident(),tuple(row[:12])))
   else:dropped+=1
namespace=dict(template.namespace);namespace.update(begin=begin,mark=mark)
namespace['batch_types']=template.original.batch_types;namespace['table']=template.original.table
exec(compile(template.source,'visibility_light_clone','exec'),namespace)
batch=namespace['batch']
def install():template.original.batch=batch
