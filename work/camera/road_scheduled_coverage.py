"""Diagnostic ordered 240x160 schedule coverage. No live adoption."""
from road_scan_schedule import *
padding=C.CDLL(str(p/'road-span-padding-segmented.dll')).nf_road_span_padding_segmented;padding.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p]
def scheduled_spans(a,b,current,bounds,table,phase):
 data=[(C.c_double*(len(r)*6))(*(v for row in r for v in row)) for r in (a,b,current)]
 ta,sa=anchor_schedule(a,bounds,table);tb,sb=anchor_schedule(b,bounds,table);schedule=apply_vertical_visibility(interpolate_schedule(a,b,bounds,table,min(r[1] for r in current),phase),current);result=[]
 for scan in schedule:
  if scan['visible_lifetime']==0:continue
  edges=(C.c_double*8)();assert span(data[2],len(current),scan['source_row'],table,edges),'Visible scan outside geometry'
  anchors=[]
  for k,records in enumerate((sa,sb)):
   if scan['ordinal']>=len(records):anchors.append(None);continue
   row=records[scan['ordinal']]['source_row'];e=(C.c_double*8)();pad=(C.c_double*2)();assert span(data[k],len((a,b)[k]),row,table,e) and padding(data[k],len((a,b)[k]),row,table,pad);anchors.append((pad[0]-e[0],pad[1]))
  if phase in (0.,1.):
   pad=(C.c_double*2)();assert padding(data[2],len(current),scan['source_row'],table,pad);start,width=pad
  elif all(v is not None for v in anchors):
   start=edges[0]+(1-phase)*anchors[0][0]+phase*anchors[1][0];width=(1-phase)*anchors[0][1]+phase*anchors[1][1]
  else:
   residual,width=anchors[0] or anchors[1];start=edges[0]+residual
  assert width>=1 and math.isfinite(start)
  result.append(dict(scan,start=start,width=width,edges=list(edges)))
 return result

def coverage_buffer(spans):
 result=[[] for _ in range(38400)]
 for scan in spans:
  start=scan['start'];end=start+2*scan['width']
  for duplicate in (1,0):
   weight=scan['visible_lifetime']*(scan['duplicate'] if duplicate else 1.)
   if weight==0:continue
   for band in range(math.floor(start/240),math.floor(math.nextafter(end,-math.inf)/240)+1):
    left=max(0.,start-band*240);right=min(240.,end-band*240);y=scan['source_row']+duplicate+band
    for row in range(max(0,math.floor(y)),min(160,math.ceil(y+1))):
     vertical=max(0.,min(row+1.,y+1)-max(row,y))
     for x in range(max(0,math.floor(left)),min(240,math.ceil(right))):
      horizontal=max(0.,min(x+1.,right)-max(x,left));alpha=weight*vertical*horizontal
      if alpha==0:continue
      d=row*240+x;old=result[d];result[d]=[(*v[:3],v[3]*(1-alpha)) for v in old if v[3]*(1-alpha)>0];result[d].append((scan['ordinal'],scan['source_row'],float(x+band*240),alpha))
 return result
