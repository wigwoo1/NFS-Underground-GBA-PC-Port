from analyze_live_stall_load import correlate
r=dict(presentation_samples=[dict(interpolated=True,hidden_window_presented=True,present_end_ns=t,display_index=i,source_older=1,refresh=2,native_commit_stage_ns=[0,0,0,90000000,91000000],draw_cpu_ns=2000000) for i,t in enumerate((0,100000000))],pause_events=[dict(begin_ns=20000000,end_ns=40000000,duration_ns=20000000)],gc_collection_samples=[dict(start_ns=10000000,end_ns=20000000)],world_preparation_stage_samples=[dict(older=1,newer=2,started_ns=0,completed_ns=100000000,construct_thread_cpu_ns=25000000,precompute_thread_cpu_ns=25000000)],timing=dict(wall_seconds=1,simulated_seconds=.98))
l=dict(thread_stopped=True,errors=[],samples=[dict(begin_ns=0,end_ns=50000000,busy_fraction=0),dict(begin_ns=50000000,end_ns=100000000,busy_fraction=1)])
a=correlate(r,l);x=a['records'][0]
assert a['gaps']==1 and x['active_gap_ms']==80 and x['gc_overlap_ms']==10 and x['load_busy_fraction']==.5 and x['load_coverage']==1 and x['callback_ms']==1
bad=dict(l,samples=l['samples']+l['samples'][:1])
try:correlate(r,bad)
except AssertionError:pass
else:raise AssertionError('Overlapping load records accepted')
print('PASS pause residual, weighted load, GC overlap and invalid load rejection')
