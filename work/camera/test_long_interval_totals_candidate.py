import copy
from owned_long_interval_totals_candidate import LongIntervalTotals
def row(i,t,g=1):return dict(native_result=1,epoch=1,generation=g,display_index=i,callback_timing=dict(draw_begin_ns=t-1000000,draw_end_ns=t-500000,present_begin_ns=t-100000,present_end_ns=t),transaction_end_ns=t+100000,prepared=dict(source_prepare_ns=123))
x=LongIntervalTotals(2)
for i,t in enumerate([1000000,17000000,57000000,97000000]):x.observe(row(i,t))
assert x.count==3 and x.long_total==2 and x.long_dropped==0
clone=copy.copy(x);clone.observe(row(4,137000000));assert clone.long_dropped==1 and x.long_dropped==0 and len(x.long_events)==2
assert [r['interval_ns'] for r in clone.stats()['long_intervals']['records']]==[40000000,40000000]
x.observe(row(9,999000000,2));assert x.excluded==1 and x.long_total==2
assert x.stats()['long_intervals']['total']==x.over33
print('PASS_BOUNDED_LONG_INTERVAL_CLOCK_COPY_EXCLUSION')
