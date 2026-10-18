"""Isolated complete bounded consumer notification timeout ledger."""
import inspect,textwrap,threading,json,time
from pathlib import Path
from live_native_hud_prefetch_generation_candidate import NativeLiveWorker
rows=[];total=0;dropped=0
started_ns=time.perf_counter_ns()
def observe(begin,end):
 global total,dropped
 assert isinstance(begin,int) and end>=begin
 total+=1
 if len(rows)<8192:rows.append(dict(begin_ns=begin,end_ns=end,thread=threading.get_ident()))
 else:dropped+=1
def save():
 out=dict(started_ns=started_ns,total=total,dropped=dropped,capacity=8192,rows=rows,scope='Actual queue.Empty returns from unchanged .01-second consumer notification wait; elapsed spans include scheduling, no CPU attribution or cadence proof.')
 path=Path('work/camera/prototype-runs/notification-timeouts-'+str(time.time_ns())+'.json');path.write_text(json.dumps(out,indent=2));print('NOTIFICATION_TIMEOUT_LEDGER',path,flush=True)
source=textwrap.dedent(inspect.getsource(NativeLiveWorker.consume))
marker='except queue.Empty:continue';assert source.count(marker)==1
source=source.replace(marker,'except queue.Empty:notification_timeout_observe(notification_wait_begin_ns,time.perf_counter_ns());continue')
namespace=dict(NativeLiveWorker.consume.__globals__,notification_timeout_observe=observe)
exec(compile(source,'isolated-notification-timeout-ledger','exec'),namespace)
NativeLiveWorker.consume=namespace['consume']
