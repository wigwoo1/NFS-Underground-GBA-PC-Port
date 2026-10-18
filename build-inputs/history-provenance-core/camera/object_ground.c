#include "object_ground.h"
#include <string.h>
static uint32_t w(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint16_t h(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static int read_index(NFVisibilityRead read,void*user,uint32_t base,unsigned index,unsigned stride,void*out,size_t size){uint64_t a=(uint64_t)base+(uint64_t)index*stride;return a<=UINT32_MAX&&a+size<=UINT64_C(0x100000000)&&read(user,(uint32_t)a,out,size);}
int nf_object_ground_height(const uint8_t state[256],unsigned region,int32_t x,int32_t z,NFVisibilityRead read,void*user,int32_t*out){
 if(!state||!read||!out||region>=512)return 0;
 uint8_t d[48],v[68],plane[20];
 if(!read_index(read,user,w(state+20),region,48,d,48))return 0;
 if(!h(d+8)&&!(d[18]&32)&&h(d+32)!=65535){unsigned next=h(d+32);if(next>=512||!read_index(read,user,w(state+20),next,48,d,48))return 0;}
 if(!read_index(read,user,w(state+16),h(d),68,v,68))return 0;
 int32_t height=(int16_t)h(v+56)+(int16_t)h(d+38),nx,ny,nz;
 if(h(d+10)!=65535){if(!read_index(read,user,w(state+28),h(d+10),20,plane,20))return 0;height+=(int16_t)h(plane+6);nx=(int16_t)h(plane+12);ny=(int16_t)h(plane+14);nz=(int16_t)h(plane+16);}
 else {nx=(int16_t)h(d+20);ny=(int16_t)h(d+22);nz=(int16_t)h(d+24);}
 if(!ny)ny=1;
 unsigned index=(unsigned)(ny<0?-ny:ny);uint32_t reciprocal;
 if(!read_index(read,user,0x08627700,index,4,&reciprocal,4))return 0;
 if(ny<0)reciprocal=0u-reciprocal;
 uint32_t slope=((uint32_t)x-w(v))*(uint32_t)nx+((uint32_t)z-w(v+4))*(uint32_t)nz;
 int64_t product=(int64_t)(int32_t)slope*(int32_t)(0u-reciprocal);
 uint32_t result=((uint32_t)height<<8)+(uint32_t)((uint64_t)product>>16);memcpy(out,&result,4);return 1;
}

