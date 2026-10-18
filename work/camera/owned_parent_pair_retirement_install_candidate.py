"""Time existing parent pair close without changing retirement order."""
import inspect,textwrap,time,json
from pathlib import Path
from live_owned_gpu_worker import LiveOwnedGPUWorker as Worker
from owned_thread_cycles import read as thread_cycles
rows=[]
original=Worker.draw_intervals
source=textwrap.dedent(inspect.getsource(original))
needle='  if self.world_pair is not None:self.world_pair.close();self.world_pair=None'
assert source.count(needle)==1
source=source.replace(needle,"  retirement_begin=time.perf_counter_ns();cycles_begin=thread_cycles();had_pair=self.world_pair is not None\n"+needle+"\n  retirement_end=time.perf_counter_ns();cycles_end=thread_cycles()\n  assert len(retirement_rows)<2048\n  retirement_rows.append(dict(source_identity=[args[5],args[3],args[1][2],args[4]],begin_ns=retirement_begin,end_ns=retirement_end,thread_cycles=cycles_end-cycles_begin,had_pair=had_pair))")
namespace=dict(original.__globals__,retirement_rows=rows,thread_cycles=thread_cycles)
exec(compile(source,'parent-pair-retirement-profile','exec'),namespace)
Worker.draw_intervals=namespace['draw_intervals']
def save():
 path=Path('work/camera/prototype-runs')/('parent-pair-retirement-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(rows=rows,capacity=2048,scope='Existing outer parent world_pair.close and assignment only, including reference release; not whole parent loop.'),indent=2));print('PARENT_PAIR_RETIREMENT',path,flush=True)
