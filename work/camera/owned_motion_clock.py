"""Exact60Hz presentation grid sampled against the original GBA cycle clock."""
HZ=16777216
REFRESH=280896
NS=1000000000
def deadline(origin,index):
 if index<0:raise ValueError('Negative display index')
 return origin+(index*NS+59)//60
def scene_samples(origin,base_refresh,older,newer,delay_refreshes=4):
 if newer<=older or older-base_refresh+delay_refreshes<0 or delay_refreshes<0:raise ValueError('Invalid scene interval')
 # Half-open source interval owns each presentation index exactly once.
 left=(older-base_refresh+delay_refreshes)*REFRESH
 right=(newer-base_refresh+delay_refreshes)*REFRESH
 first=(left*60+HZ-1)//HZ;end=(right*60+HZ-1)//HZ
 return [dict(index=i,deadline_ns=deadline(origin,i),alpha=(i*HZ-left*60)/((right-left)*60)) for i in range(first,end)]
