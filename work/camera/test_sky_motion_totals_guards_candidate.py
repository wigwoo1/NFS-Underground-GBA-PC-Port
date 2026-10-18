import copy,json
from pathlib import Path
from owned_sky_motion_totals_candidate import SkyMotionTotals

def row(i,alpha,angles=(0,4)):
 phase=(((angles[1]&16383) if alpha==1 else (angles[0]&16383)+(((angles[1]-angles[0]+8192)&16383)-8192)*alpha)*240/4096)%240
 return dict(native_result=1,sky_source_angles=angles,alpha=alpha,sky_fraction=phase%1,epoch=1,generation=1,display_index=i,native_committed_sample=[0]*6+[i*16666667],callback_timing=dict(present_end_ns=i*16666667))
for angles in ((0,4),(16382,2),(2,16382)):
 t=SkyMotionTotals()
 for i in range(60):t.observe(row(i,i/59,angles))
 assert t.samples==60 and t.transitions==59 and t.stationary==0
hold=SkyMotionTotals()
for i in range(60):hold.observe(row(i,i/59,(5,5)))
assert hold.stationary==hold.source_holds==59
assert hold.stats()['stationary_with_moving_source_angles']==0
moving_hold=SkyMotionTotals()
for i in range(3):moving_hold.observe(row(i,.5))
assert moving_hold.stats()['stationary_with_moving_source_angles']==2
budget=SkyMotionTotals()
a=row(0,0);b=row(1,.2);c=row(2,.4)
a['native_committed_sample'][6]=0;a['callback_timing']['present_end_ns']=0
b['native_committed_sample'][6]=16666666;b['callback_timing']['present_end_ns']=16666667
c['native_committed_sample'][6]=41666666;c['callback_timing']['present_end_ns']=41666667
for x in (a,b,c):budget.observe(x)
stats=budget.stats()
assert stats['commit_intervals_over_60fps_budget']==1 and stats['api_intervals_over_60fps_budget']==2
assert stats['maximum_commit_gap_ns']==25000000 and stats['commit_intervals_over_25ms']==0
snapshot=copy.copy(budget);d=row(3,.6);d['generation']=2;budget.observe(d)
assert budget.excluded==1 and snapshot.excluded==0 and snapshot.stats()==stats
assert stats['commit_interval_buckets']==[0,1,0,1,0,0]
assert stats['api_interval_buckets']==[0,1,0,1,0,0]
assert sum(stats['commit_interval_buckets'])==stats['adjacent_transitions']
isolated=stats['commit_interval_buckets'];isolated[0]=999
assert budget.stats()['commit_interval_buckets'][0]==0
for cutoff,index in ((16000000,0),(17333334,1),(20000000,2),(25000000,3),(33333334,4)):
 assert SkyMotionTotals._bucket((0,)*6,cutoff)[index]==1
 assert SkyMotionTotals._bucket((0,)*6,cutoff+1)[index+1]==1
rejected=[]
for name,change in [('wrong_fraction',dict(sky_fraction=.9)),('negative_alpha',dict(alpha=-1)),('large_alpha',dict(alpha=2)),('nan_alpha',dict(alpha=float('nan'))),('negative_angle',dict(sky_source_angles=(-1,4)))]:
 t=SkyMotionTotals();bad=row(0,.5);bad.update(change)
 try:t.observe(bad)
 except AssertionError:rejected.append(name)
 else:raise AssertionError(name)
 assert t.samples==0 and t.previous is None
out=dict(result='PASS_SKY_TOTALS_GUARDS',wrap_directions=2,small_motion_transitions=59,legitimate_holds=59,rejected=rejected,scope='Synthetic phase/counter validation, not GPU pixels or gameplay.')
Path('work/camera/prototype-runs/sky-totals-guards-20261008.json').write_text(json.dumps(out,indent=2));print(out)
