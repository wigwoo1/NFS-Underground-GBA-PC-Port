"""Bounded parent publication tail timings; no queued pixels or disk writes."""
import time,json
from pathlib import Path
import owned_progressive_retirement_install_candidate as retirement
rows=[]
import owned_hud_pair_lookahead_install_candidate as lookahead
source=lookahead.source
needle='   self.results.append(row)'
assert source.count(needle)==1
source=source.replace(needle,"   tail_begin=time.perf_counter_ns();tail_cycles=thread_cycles()\n"+needle+"\n   tail_end=time.perf_counter_ns();tail_cycles_end=thread_cycles()\n   assert len(tail_rows)<8192\n   tail_rows.append(dict(identity=[epoch,generation,slot['index']],commit_ns=row['commit'][6],transaction_end_ns=row['transaction_end_ns'],append_begin_ns=tail_begin,append_end_ns=tail_end,append_cycles=tail_cycles_end-tail_cycles,native_transaction_end_ns=row['native_transaction']['transaction_end_ns'],renderer_dispatch=dict(row['native_transaction']['renderer_dispatch']),native_stage_ns=list(row['native_transaction']['stages']),return_execution=row['native_transaction'].get('return_execution')))")
namespace=dict(retirement.owned_draw.__globals__,tail_rows=rows)
exec(compile(source,'parent-publication-tail','exec'),namespace)
retirement.owned_draw=namespace['_draw_intervals']
def save():
 path=Path('work/camera/prototype-runs')/('parent-publication-tail-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(rows=rows,capacity=8192,scope='Parent diagnostic append elapsed/raw thread cycles, exact native identity. Does not cover postfunction retirement or reference destruction.'),indent=2));print('PARENT_PUBLICATION_TAIL',path,flush=True)
