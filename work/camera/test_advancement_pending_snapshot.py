import struct
from owned_advancement_batch_publication import AdvancementBatchPublication
bits=struct.unpack('<Q',struct.pack('<d',.5))[0]
sample=[1,2,100,104,10,bits,1000,1]
previous=dict(epoch=1,generation=2,source_older=100,refresh=104,display_index=10,alpha=.5)
plan=dict(previous_index=10,target_index=14,skipped_count=3,last_skipped_deadline_ns=200,observed_ns=201)
rows=[dict(epoch=1,generation=2,source_older=104,refresh=108,display_index=i,alpha=.5,display_advance_plan=plan if i==14 else None) for i in (14,15)]
p=AdvancementBatchPublication();p.last=previous;p.begin(1,2,rows,object())
s=p.snapshot(sample,1,1,2);assert s['pending_indices']==[14,15] and s['last_committed']['display_index']==10
for key,value in [('previous_index',9),('target_index',15),('skipped_count',2),('observed_ns',199)]:
 original=plan[key];plan[key]=value
 try:p.snapshot(sample,1,1,2)
 except ValueError:pass
 else:raise AssertionError(key)
 plan[key]=original
from owned_batch_commit_snapshot import resolve_pause_snapshot
try:resolve_pause_snapshot(sample,1,1,2,rows,previous)
except ValueError:pass
else:raise AssertionError('Default strict checker weakened')
print('PASS pending advanced snapshot and four invalid plans; default remains strict')
