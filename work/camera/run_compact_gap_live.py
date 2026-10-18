"""Diagnostic live entry; current prepared HUD and original clock unchanged."""
import sys,gc,time,json,threading
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'work/camera'))
from owned_compact_gap_trace import install as install_expanded
import os
if os.environ.get('NFSUG_COMPACT_GAP_TRACE', '1') == '1':
    install_expanded()
else:
    import owned_fine_deadline_trace as trace
    import owned_native_transaction_interval_totals_candidate as totals
    assert totals.LongIntervalTotals is trace.DeadlineTrace
    totals.LongIntervalTotals = trace.Base
events=[];active={};dropped=0
def observe(phase,info):
    global dropped
    key=(threading.get_ident(),info['generation'])
    if phase=='start':active[key]=time.perf_counter_ns()
    elif phase=='stop':
        end=time.perf_counter_ns();begin=active.pop(key,None)
        if begin is None:return
        if len(events)<1024:events.append(dict(start_ns=begin,end_ns=end,thread=key[0],generation=key[1],collected=info.get('collected',0)))
        else:dropped+=1
source=(root/'work/camera/run_prepared_hud_packaged.py').read_text()
late_marker=' install_fused()\\\\n'
assert source.count(late_marker)==1
source=source.replace(late_marker,' install_fused()\\\\n from owned_prepared_hud_return_boundaries import install as install_hud_return\\\\n install_hud_return()\\\\n from owned_session_post_consumer_install import install as install_inner_session\\\\n install_inner_session()\\\\n from owned_borrowed_metadata_boundaries import install as install_metadata\\\\n install_metadata()\\\\n')
marker=' import owned_present_batch_trace_install_candidate\\n'
injection=marker+' from owned_consumer_stage_boundaries_candidate import install as install_consumer_boundaries\\n install_consumer_boundaries()\\n from owned_post_render_boundaries_candidate import install as install_post_render\\n install_post_render()\\n'
old='source=pathlib.Path(path).read_text();marker='
assert source.count(old)==1
source=source.replace(old,'source=pathlib.Path(path).read_text();assert source.count('+repr(marker)+')==1;source=source.replace('+repr(marker)+','+repr(injection)+');marker=')
gc.callbacks.append(observe)
try:exec(compile(source,str(root/'work/camera/run_prepared_hud_packaged.py'),'exec'),dict(__name__='__main__',__file__=str(root/'work/camera/run_prepared_hud_packaged.py')))
finally:
    gc.callbacks.remove(observe)
    path=root/'work/camera/prototype-runs'/('consumer-boundaries-parent-gc-'+str(time.time_ns())+'.json')
    path.write_text(json.dumps(dict(events=events,dropped=dropped,scope='Bounded parent collection callbacks, policy unchanged. Overlap not exclusive causation.'),indent=2))
    print('PARENT_GC_TRACE',path)



