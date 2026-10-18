"""Opt-in bounded wall/cycle measurements around the actual native projection call."""
import time
from owned_thread_cycles import read
rows=[];calls=0;dropped=0;total_ns=0;max_ns=0
def measure(function,*args):
 global calls,dropped,total_ns,max_ns
 cycles=read();begin=time.perf_counter_ns();result=function(*args);end=time.perf_counter_ns();spent=end-begin;used=read()-cycles
 calls+=1;total_ns+=spent;max_ns=max(max_ns,spent)
 if spent>10000000:
  if len(rows)<512:rows.append(dict(begin_ns=begin,end_ns=end,wall_ns=spent,thread_cycles=used,result=result))
  else:dropped+=1
 return result
def snapshot():
 captured=list(rows);rows.clear()
 return dict(calls=calls,total_ns=total_ns,max_ns=max_ns,dropped=dropped,long_calls=captured,scope='Actual ctypes native projection call wall scope includes native execution and GIL reacquisition; cycles are same-thread CPU evidence, not exclusive waiting cause.')
