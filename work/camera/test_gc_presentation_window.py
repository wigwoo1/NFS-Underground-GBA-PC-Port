from analyze_gc_presentation_window import analyze
r=dict(presentation_samples=[dict(native_committed_sample=[0]*6+[10],present_end_ns=20)],gc_collection_samples=[dict(start_ns=a,end_ns=b) for a,b in [(0,10),(9,12),(12,18),(18,22),(20,30)]])
a=analyze(r);assert [len(a['groups'][k]) for k in ('before','overlapping','after')]==[1,3,1]
assert [x['window_overlap_ms']*1e6 for x in a['groups']['overlapping']]==[2,6,2]
print('PASS startup, active, crossing and shutdown collection boundaries')
