"""Bounded opt-in child collection timing; no collector policy changes."""
import gc,time,threading
rows=[];active={};dropped=0
def observe(phase,info):
 global dropped
 key=(threading.get_ident(),info['generation'])
 if phase=='start':active[key]=time.perf_counter_ns()
 elif phase=='stop':
  end=time.perf_counter_ns();begin=active.pop(key,None)
  if begin is None:return
  row=dict(start_ns=begin,end_ns=end,generation=key[1],thread=key[0],collected=info.get('collected'),uncollectable=info.get('uncollectable'))
  if len(rows)<512:rows.append(row)
  else:dropped+=1
def snapshot(begin,end):
 count=len(rows);captured=rows[:count];del rows[:count]
 return dict(dropped=dropped,rows=captured,request_begin_ns=begin,request_end_ns=end,scope='Completed collections drained once at each request terminal; includes between-request events; no exclusive cause claim')
if observe not in gc.callbacks:gc.callbacks.append(observe)
