"""Scheduled current-pose indexed material component; nearest color remains discontinuous."""
from road_scheduled_coverage import scheduled_spans,coverage_buffer
from road_temporal_sampler import uv,pair_query,compose_palette,C,math,struct

def sample_buffer(a,b,current,bounds,table,phase,texture,normalization,palettes):
 spans=scheduled_spans(a,b,current,bounds,table,phase);by_ordinal={s['ordinal']:s for s in spans};coverage=coverage_buffer(spans)
 width,height=struct.unpack_from('<2I',texture);plane=texture[8:];assert len(plane)==width*height and len(palettes)==160*512
 result=[];cache={}
 for destination,items in enumerate(coverage):
  contributors=[]
  for ordinal,row,x,weight in items:
   scan=by_ordinal[ordinal];key=(ordinal,x)
   if key not in cache:
    relative=max(0.,min(x-scan['start'],math.nextafter(2*scan['width'],0.)));pair=C.c_double();assert pair_query(scan['width'],relative,C.byref(pair));edges=scan['edges'];sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),scan['width'],pair.value,table,sample)
    tx=(2*math.floor(sample[0]/(65536*normalization[0])*(width/2))+int(x)%2)%width;ty=math.floor(sample[1]/(65536*normalization[1])*height)%height
    cache[key]=dict(uv=list(sample),index=plane[ty*width+tx])
   contributors.append(dict(cache[key],weight=weight,source_row=row,source_x=x))
  palette=palettes[(destination//240)*512:(destination//240+1)*512];result.append(compose_palette(contributors,palette))
 return result

def sample_filtered_buffer(a,b,current,bounds,table,phase,texture,normalization,palettes,destinations=None):
 if phase in (0.,1.):
  full=sample_buffer(a,b,current,bounds,table,phase,texture,normalization,palettes);return full if destinations is None else [full[d] for d in destinations]
 spans=scheduled_spans(a,b,current,bounds,table,phase);maps=[{s['ordinal']:s for s in scheduled_spans(r,r,r,bounds,table,0.)} for r in (a,b)];by_ordinal={s['ordinal']:s for s in spans};coverage=coverage_buffer(spans)
 width,height=struct.unpack_from('<2I',texture);plane=texture[8:];assert len(plane)==width*height and len(palettes)==160*512
 def coordinate(scan,relative):
  relative=max(0.,min(relative,math.nextafter(2*scan['width'],0.)));pair=C.c_double();assert pair_query(scan['width'],relative,C.byref(pair));e=scan['edges'];sample=(C.c_double*2)();assert uv((C.c_double*3)(*e[1:4]),(C.c_double*3)(*e[5:8]),scan['width'],pair.value,table,sample)
  return [sample[0]/(65536*normalization[0])*(width/2),sample[1]/(65536*normalization[1])*height]
 result=[];cache={}
 for d in (range(38400) if destinations is None else destinations):
  items=coverage[d]
  contributors=[]
  for ordinal,row,x,weight in items:
   key=(ordinal,x)
   if key not in cache:
    scan=by_ordinal[ordinal];relative=x-scan['start'];v=coordinate(scan,relative)
    # Fixed source-pixel anchor residuals are continuous between integer queries.
    # Flooring the UV at a moving relative query would introduce step changes.
    base=math.floor(relative);fraction=relative-base;residuals=[]
    for m in maps:
     if ordinal not in m:residuals.append(None);continue
     ca=coordinate(m[ordinal],base);cb=coordinate(m[ordinal],base+1)
     residuals.append([(1-fraction)*(math.floor(ca[k])-ca[k])+fraction*(math.floor(cb[k])-cb[k]) for k in range(2)])
    if residuals[0] is None:residuals[0]=residuals[1]
    if residuals[1] is None:residuals[1]=residuals[0]
    v=[v[k]+(1-phase)*residuals[0][k]+phase*residuals[1][k] for k in range(2)]
    ix,iy=map(math.floor,v);fx,fy=v[0]-ix,v[1]-iy;cache[key]=[]
    for dx in (0,1):
     for dy in (0,1):
      w=(fx if dx else 1-fx)*(fy if dy else 1-fy);index=plane[((iy+dy)%height)*width+(2*(ix+dx)+int(x)%2)%width];cache[key].append((index,w))
   contributors.extend(dict(index=index,weight=weight*w) for index,w in cache[key] if w)
  result.append(compose_palette(contributors,palettes[(d//240)*512:(d//240+1)*512]))
 return result
