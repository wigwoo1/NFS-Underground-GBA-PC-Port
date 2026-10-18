"""Experimental source-row anchored palette-color filtering, diagnostic only."""
from road_temporal_sampler import *
def sample_filtered(a,na,b,nb,current,nc,bounds,phase,table,destination,texture,normalization,palette):
 color,contributors=sample_temporal(a,na,b,nb,current,nc,bounds,phase,table,destination,texture,normalization,palette)
 if phase in (0.,1.):return color,contributors
 width,height=struct.unpack_from('<2I',texture);plane=texture[8:];rgb=[0.,0.,0.]
 def coordinate(ring,count,row,x):
  pad=(C.c_double*2)();edges=(C.c_double*8)();assert padding(ring,count,ring,count,ring,count,row,0.,table,pad);assert span(ring,count,row,table,edges)
  relative=max(0.,min(x-pad[0],math.nextafter(2*pad[1],0.)));pair=C.c_double();assert pair_query(pad[1],relative,C.byref(pair));sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],pair.value,table,sample)
  return [sample[0]/(65536*normalization[0])*(width/2),sample[1]/(65536*normalization[1])*height]
 for c in contributors:
  row,x=c['source_row'],c['source_x'];ca=coordinate(a,na,row,x);cb=coordinate(b,nb,row,x);v=[c['uv'][0]/(65536*normalization[0])*(width/2),c['uv'][1]/(65536*normalization[1])*height]
  # Correct texture phase by source-pose endpoint residuals. Fixed lane is
  # preserved; interpolate palette RGB after each indexed lookup.
  v=[v[k]+(1-phase)*(math.floor(ca[k])-ca[k])+phase*(math.floor(cb[k])-cb[k]) for k in range(2)]
  ix,iy=map(math.floor,v);fx,fy=v[0]-ix,v[1]-iy;filtered=[0.,0.,0.]
  for dx in (0,1):
   for dy in (0,1):
    weight=(fx if dx else 1-fx)*(fy if dy else 1-fy);tx=(2*(ix+dx)+int(x)%2)%width;ty=(iy+dy)%height;index=plane[ty*width+tx];word=struct.unpack_from('<H',palette,index*2)[0]
    for channel in range(3):
     q=(word>>(channel*5))&31;filtered[channel]+=weight*((q<<3)|(q>>2))
  c['filtered_coordinate']=v;c['filtered_rgb']=filtered
  for channel in range(3):rgb[channel]+=c['weight']*filtered[channel]
 return (*rgb,color[3]),contributors
