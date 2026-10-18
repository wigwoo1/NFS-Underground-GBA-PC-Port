"""Bounded snapshot retirement diagnostic; unchanged release semantics."""
import threading,time,json
from pathlib import Path
from owned_thread_cycles import read
from owned_hud_shared_library_binding_candidate import HudFrameSnapshot
original=HudFrameSnapshot.close
lock=threading.Lock();rows=[];total=0;dropped=0
def close(self):
 global total,dropped
 begin=time.perf_counter_ns();cycles=read();was_closed=self.closed
 try:return original(self)
 finally:
  end=time.perf_counter_ns();last=read()
  if not was_closed:
   row=dict(thread=threading.get_ident(),epoch=self.epoch,refresh=self.refresh,begin_ns=begin,end_ns=end,wall_ns=end-begin,thread_cycles=last-cycles,closed=self.closed)
   with lock:
    total+=1
    if len(rows)<512:rows.append(row)
    else:dropped+=1
HudFrameSnapshot.close=close
def save():
 with lock:
  out=dict(total=total,dropped=dropped,rows=list(rows),scope='Snapshot.close wrapper wall/cycles; unchanged native release, bounded scalar rows, diagnostic perturbs timing.')
 path=Path('work/camera/prototype-runs/hud-snapshot-retire-'+str(time.time_ns())+'.json');path.write_text(json.dumps(out,indent=2));return str(path)
