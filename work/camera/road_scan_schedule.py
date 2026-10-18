"""Diagnostic source-scan ordinal scheduling; not a final visibility policy.
Ordinals are original traversal positions within one world-road source.
No projected polygon correspondence or game-timing changes.
"""
import ctypes as C,math
from pathlib import Path
p=Path(__file__).resolve().parent
span=C.CDLL(str(p/'road-span-transition-at.dll')).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p]
def anchor_schedule(ring,bounds,table):
 assert 3<=len(ring)<=64 and all(math.isfinite(v) for r in ring for v in r)
 assert all(r[1]==math.floor(r[1]) for r in ring)
 data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));top=min(160.,min(r[1] for r in ring));row=int(max(bounds[2],top));doubled=False;result=[]
 while row<=bounds[3]:
  edges=(C.c_double*8)()
  if span(data,len(ring),row,table,edges):
   doubled=doubled or edges[3]>49152
   result.append(dict(ordinal=len(result),source_row=float(row),duplicate=float(doubled),lifetime=1.))
  row+=2 if doubled else 1
 return top,result

def interpolate_schedule(a,b,bounds,table,current_top,phase):
 assert math.isfinite(phase) and 0<=phase<=1 and math.isfinite(current_top)
 ta,sa=anchor_schedule(a,bounds,table);tb,sb=anchor_schedule(b,bounds,table)
 if phase==0:return sa
 if phase==1:return sb
 result=[]
 for ordinal in range(max(len(sa),len(sb))):
  aa=sa[ordinal] if ordinal<len(sa) else None;bb=sb[ordinal] if ordinal<len(sb) else None
  if aa and bb:
   ra=aa['source_row']-ta;rb=bb['source_row']-tb;relative=ra+(rb-ra)*phase;duplicate=aa['duplicate']+(bb['duplicate']-aa['duplicate'])*phase;lifetime=1.
  else:
   item=aa or bb;relative=item['source_row']-(ta if aa else tb);duplicate=item['duplicate'];lifetime=1-phase if aa else phase
  result.append(dict(ordinal=ordinal,source_row=current_top+relative,duplicate=duplicate,lifetime=lifetime))
 return result

def apply_vertical_visibility(schedule,current_ring):
 """Source scan footprint overlap with current source-row extent.
 Keep scan identity/lifetime metadata; zero overlap is explicit geometry
 invisibility, not a missing-span fallback. Does not establish horizontal
 pixel coverage, near-vertex span sampling or material correspondence.
 """
 assert current_ring and all(math.isfinite(r[1]) for r in current_ring)
 top=min(r[1] for r in current_ring);bottom=max(r[1] for r in current_ring);result=[]
 for scan in schedule:
  row=scan['source_row'];coverage=max(0.,min(row+1.,bottom)-max(row,top));coverage=min(1.,coverage)
  result.append(dict(scan,vertical_coverage=coverage,visible_lifetime=scan['lifetime']*coverage))
 return result
