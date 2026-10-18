from analyze_active_play_cadence import analyze
r=dict(pause_events=[dict(begin_ns=20000000,end_ns=220000000,duration_ns=200000000)],timing=dict(wall_seconds=1.,simulated_seconds=.8),presentation_samples=[dict(interpolated=True,hidden_window_presented=True,display_index=i,present_end_ns=t) for i,t in enumerate([0,16666667,233333334,250000001,300000001])])
a=analyze(r);assert a['active_clock_ratio']==1 and a['active_gap_count']==4 and a['active_gaps_over_two_refreshes']==1 and len(a['excluded_pause_crossings'])==1 and a['contiguous']
# A long unpaused residual must remain a failure even when crossing a pause.
r['presentation_samples'][2]['present_end_ns']=430000000
r['presentation_samples'][3]['present_end_ns']=446666667
r['presentation_samples'][4]['present_end_ns']=463333334
a=analyze(r)
assert a['active_gaps_over_two_refreshes']==1
assert abs(a['active_gap_max_ms']-213.333333)<1e-6
assert a['excluded_pause_crossings'][0]['nonpause_residual_ms']>200
r['pause_events'][0]['duration_ns']=1
try:analyze(r)
except AssertionError:pass
else:raise AssertionError('Bad pause accepted')
print('PASS pause-crossing separation, real-stall retention, clock correction and malformed-pause rejection')
