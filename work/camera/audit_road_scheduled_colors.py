from pathlib import Path
import ctypes as C,json,sys
from actual_road_interval_geometry import interval_ring,bounds
from road_scheduled_sampler import sample_filtered_buffer
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());palettes=(p/'stable-road-display-palettes.bin').read_bytes();cmd=7;begin=8768;texture=(p/'road-7-index-texture.bin').read_bytes();a=interval_ring(cmd,begin,0.,table);b=interval_ring(cmd,begin,1.,table);pixels=[25211+dy*240+dx for dy in (-1,0,1) for dx in (-1,0,1)];cache={}
def evaluate(t):
 if t not in cache:
  ring=interval_ring(cmd,begin,t,table);cache[t]=sample_filtered_buffer(a,b,ring,bounds[cmd],table,t,texture,(128,64),palettes,pixels)
 return cache[t]
def gap(x,y):return max(abs(v-w) for a,b in zip(evaluate(x),evaluate(y)) for v,w in zip(a[:3],b[:3]))
phases=[i/32 for i in range(33)];brackets=sorted([(gap(x,y),x,y) for x,y in zip(phases,phases[1:])],reverse=True)[:4];checks=[]
for initial,lo,hi in brackets:
 for step in range(26):
  mid=(lo+hi)/2
  if gap(lo,mid)>=gap(mid,hi):hi=mid
  else:lo=mid
 checks.append(dict(initial_gap=initial,lo=lo,hi=hi,phase_width=hi-lo,final_channel_gap=gap(lo,hi)))
r=dict(result='LOCALIZED_COLOR_JUMP_FOUND' if any(v['final_channel_gap']>.01 for v in checks) else 'NO_LOCALIZED_JUMP_FOUND',command=cmd,begin=begin,pixels=pixels,checks=checks,evaluations=len(cache),scope='Nine destinations, one actual interval; adaptive highest-gap brackets only, not exhaustive global continuity.')
(p/('road-scheduled-colors-'+sys.argv[1]+'.json')).write_text(json.dumps(r,indent=2));print(json.dumps(r))
