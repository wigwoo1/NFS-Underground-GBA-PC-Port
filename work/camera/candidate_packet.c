#include "scene_packet.h"
#include <stdlib.h>
#include <string.h>
static uint32_t get32(const void*p){uint32_t v;memcpy(&v,p,4);return v;}
static void put32(void*p,uint32_t v){memcpy(p,&v,4);}
/* Unlit owned candidate only; caller verifies asset/scene and anchor meaning.
   before is command position, not surface index. Output failure is atomic. */
static int insert_unlit_surface(const void*packet,size_t bytes,
 const void*surface,size_t surface_bytes,const uint32_t identity[5],unsigned before,
 void**out,size_t*out_bytes,unsigned kind){
 NFScenePacket p;if(!surface||!identity||!out||!out_bytes||surface_bytes<12||surface_bytes>5*1024*1024||!nf_scene_packet_view(packet,bytes,&p))return 0;
 unsigned count=get32(p.section[1].data+4);
 if(count>=128||before>count||identity[0]!=kind||identity[4])return 0;
 for(unsigned i=0;i<count;i++)if(!memcmp(p.section[4].data+8+i*20,identity,20))return 0;
 unsigned vertices=get32(surface),w=get32((const uint8_t*)surface+4),h=get32((const uint8_t*)surface+8);
 if(vertices<3||vertices>32||!w||w>1024||!h||h>1024||12+vertices*40ull+w*h*4ull!=surface_bytes)return 0;
 uint8_t*owned[4]={0};size_t sizes[4]={p.section[1].size+surface_bytes,p.section[2].size+4,p.section[3].size+4,p.section[4].size+20};int ok=0;
 for(unsigned i=0;i<4;i++){owned[i]=malloc(sizes[i]);if(!owned[i])goto done;}
 memcpy(owned[0],p.section[1].data,p.section[1].size);memcpy(owned[0]+p.section[1].size,surface,surface_bytes);put32(owned[0]+4,count+1);
 memcpy(owned[1],p.section[2].data,8+before*4);put32(owned[1]+8+before*4,count);memcpy(owned[1]+12+before*4,p.section[2].data+8+before*4,p.section[2].size-8-before*4);put32(owned[1]+4,count+2);
 size_t prefix=p.section[3].size-131072;
 memcpy(owned[2],p.section[3].data,prefix);put32(owned[2]+prefix,0);memcpy(owned[2]+prefix+4,p.section[3].data+prefix,131072);put32(owned[2]+4,count+1);
 prefix=p.section[4].size-20;
 memcpy(owned[3],p.section[4].data,prefix);memcpy(owned[3]+prefix,identity,20);memcpy(owned[3]+prefix+20,p.section[4].data+prefix,20);put32(owned[3]+4,count+2);
 for(unsigned i=0;i<4;i++)p.section[i+1]=(NFSceneSection){owned[i],sizes[i]};
 ok=nf_scene_packet_build(&p,out,out_bytes);
done:for(unsigned i=0;i<4;i++)free(owned[i]);return ok;
}

int nf_scene_packet_insert_wall(const void*p,size_t n,const void*s,size_t sn,const uint32_t id[5],unsigned before,void**out,size_t*bytes){return insert_unlit_surface(p,n,s,sn,id,before,out,bytes,2);}
int nf_scene_packet_insert_road(const void*p,size_t n,const void*s,size_t sn,const uint32_t id[5],unsigned before,void**out,size_t*bytes){return insert_unlit_surface(p,n,s,sn,id,before,out,bytes,1);}
