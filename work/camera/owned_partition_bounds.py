"""Recovered clip-record bounds from projected raw portal endpoints."""
def bounds(left,right,near_flags,parent_left,parent_right):
 return (2 if near_flags&8 else max(left,parent_left),238 if near_flags&16 else min(right,parent_right))

def record(descriptor,left,right,near_flags,parent,top,bottom,point_flags,first_depth,second_depth):
 left,right=bounds(left,right,near_flags,parent[1],parent[2])
 flags=parent[5]&128
 if point_flags&0x800:flags=128
 if min(first_depth,second_depth)>0x800:flags|=1
 return (descriptor&65535,left&65535,right&65535,top&65535,bottom&65535,flags,(parent[6]+1)&65535)
