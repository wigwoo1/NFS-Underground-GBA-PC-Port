"""Diagnostic temporal source-write texture sampling; no live adoption."""
from pathlib import Path
import ctypes as C,math,struct
from road_lattice_sampler import uv,compose_palette
p=Path(__file__).resolve().parent
writes=C.CDLL(str(p/'road-temporal-writes.dll')).nf_road_temporal_writes;writes.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
padding=C.CDLL(str(p/'road-temporal-padding.dll')).nf_road_temporal_padding;padding.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p]
span=C.CDLL(str(p/'road-span-transition-at.dll')).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p]
pair_query=C.CDLL(str(p/'road-pair-query-continuous.dll')).nf_road_pair_query_continuous;pair_query.argtypes=[C.c_double,C.c_double,C.c_void_p]
def sample_temporal(a,na,b,nb,current,nc,bounds,phase,table,destination,texture,normalization,palette):
 items=(C.c_double*(322*3))();count=C.c_uint();assert writes(a,na,b,nb,current,nc,(C.c_uint16*4)(*bounds),phase,table,destination,items,322,C.byref(count)),'Unsupported temporal schedule'
 width,height=struct.unpack_from('<2I',texture);plane=texture[8:];contributors=[]
 for i in range(count.value):
  row,x,weight=items[i*3:i*3+3];pad=(C.c_double*2)();edges=(C.c_double*8)();assert padding(a,na,b,nb,current,nc,row,phase,table,pad);assert span(current,nc,row,table,edges)
  relative=max(0.,min(x-pad[0],math.nextafter(2*pad[1],0.)));pair=C.c_double();assert pair_query(pad[1],relative,C.byref(pair));sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],pair.value,table,sample)
  tx=(2*math.floor(sample[0]/(65536*normalization[0])*(width/2))+int(x)%2)%width;ty=math.floor(sample[1]/(65536*normalization[1])*height)%height
  contributors.append(dict(source_row=row,source_x=x,weight=weight,pair=pair.value,pair_width=pad[1],uv=list(sample),index=plane[ty*width+tx]))
 return compose_palette(contributors,palette),contributors
