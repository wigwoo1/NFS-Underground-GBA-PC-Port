#include <stdio.h>
#include "scene_packet.h"
#include <string.h>
#include <math.h>
#include <stdlib.h>
static uint32_t word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint16_t half(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static int finite_doubles(const uint8_t*p,size_t n){for(size_t i=0;i<n;i++){double v;memcpy(&v,p+i*8,8);if(!isfinite(v))return 0;}return 1;}
static void put_word(uint8_t*p,uint32_t value){memcpy(p,&value,4);}
static int validate_model(const uint8_t*m,size_t ms){

 if(ms<160||word(m)!=0x324d464e)return 0;
 unsigned vertices=word(m+4),faces=word(m+8),corners=word(m+12),mw=word(m+16),mh=word(m+20);
 if(!vertices||vertices>2048||!faces||faces>512||corners>4096||!mw||mw>1024||!mh||mh>1024)return 0;
 uint64_t expected=160ull+vertices*24ull+faces+corners*18ull+mw*mh*4ull;
 if(expected!=ms){
  if(expected>ms||ms-expected!=16ull+mw*mh||word(m+expected)!=0x31495a4e||word(m+expected+4)!=mw||word(m+expected+8)!=mh||word(m+expected+12))return 0;
 }
 if(!finite_doubles(m+24,17+vertices*3))return 0;
 size_t face_offset=160+vertices*24;unsigned total=0;
 for(unsigned i=0;i<faces;i++){unsigned n=m[face_offset+i];if(n<3||n>32)return 0;total+=n;}if(total!=corners)return 0;
 const uint8_t*indices=m+face_offset+faces;for(unsigned i=0;i<corners;i++)if(half(indices+i*2)>=vertices)return 0;
 if(!finite_doubles(indices+corners*2,corners*2))return 0;
 return 1;
}
int nf_scene_model_indices(NFSceneSection model,const uint8_t**indices,size_t*size){
 if(!indices||!size||!model.data||!validate_model(model.data,model.size))return 0;
 const uint8_t*m=model.data;size_t pixels=(size_t)word(m+16)*word(m+20);
 size_t base=160+(size_t)word(m+4)*24+word(m+8)+(size_t)word(m+12)*18+pixels*4;
 if(model.size==base)return 0;
 *indices=m+base+16;*size=pixels;return 1;
}
int nf_scene_model_attach_indices(NFSceneSection model,const uint8_t*indices,size_t size,void**out,size_t*out_size){
 if(!out||!out_size||!indices||!model.data||!validate_model(model.data,model.size))return 0;
 const uint8_t*m=model.data;size_t pixels=(size_t)word(m+16)*word(m+20);
 size_t base=160+(size_t)word(m+4)*24+word(m+8)+(size_t)word(m+12)*18+pixels*4;
 if(size!=pixels||model.size!=base)return 0;
 uint8_t*copy=malloc(base+16+pixels);if(!copy)return 0;
 memcpy(copy,m,base);put_word(copy+base,0x31495a4e);put_word(copy+base+4,word(m+16));put_word(copy+base+8,word(m+20));put_word(copy+base+12,0);memcpy(copy+base+16,indices,pixels);
 *out=copy;*out_size=base+16+pixels;return 1;
}
/* NWI1 trailer: count, then mode/size/indices for each world surface.
   mode0 legacy, mode1 road indices, mode2 wall base classifications,
   mode3 wall base plus16lighting classifications, mode4 affine road indices,
   modes5/6 perspective/affine indices plus288byte raw source attributes. */
int nf_scene_road_attributes_match(NFSceneSection surface,const NFRoadSourceAttributes*raw){
 if(!surface.data||surface.size<12||!raw)return 0;const uint8_t*p=surface.data;unsigned count=word(p),width=word(p+4),height=word(p+8);
 if(count<3||count>32||width<1||width>1024||height<1||height>1024||surface.size!=12ull+count*40ull+width*height*4ull||!finite_doubles(p+12,count*5))return 0;
 if(raw->count!=count||raw->shift>10||(1u<<raw->shift)!=width||raw->stored_height!=height*2||raw->affine>1||!raw->material||!raw->animation||(raw->material&3)||(raw->animation&1)||raw->offsets[0]<-32768||raw->offsets[0]>32767||raw->offsets[1]<-32768||raw->offsets[1]>32767)return 0;
 for(unsigned i=count;i<32;i++)if(raw->attributes[i][0]||raw->attributes[i][1])return 0;
 const uint8_t*uv=p+12+count*24;
 for(unsigned i=0;i<count;i++){
  double actual[2];memcpy(actual,uv+i*16,16);
  double expected[2]={raw->attributes[i][0]/16384.0+raw->offsets[0]/(256.0*width),raw->attributes[i][1]/16384.0+raw->offsets[1]/(512.0*height)};
  if(fabs(actual[0]-expected[0])>1e-10||fabs(actual[1]-expected[1])>1e-10){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))fprintf(stderr,"road_attribute_uv_mismatch vertex=%u count=%u width=%u height=%u actual=%.17g,%.17g expected=%.17g,%.17g offsets=%d,%d raw=%d,%d\n",i,count,width,height,actual[0],actual[1],expected[0],expected[1],raw->offsets[0],raw->offsets[1],raw->attributes[i][0],raw->attributes[i][1]);return 0;}
 }
 return 1;
}
static int world_layout(NFSceneSection section,size_t*base,unsigned*count,unsigned widths[128],unsigned heights[128],unsigned corners_out[128]){
 const uint8_t*p=section.data;size_t pos=8;if(!p||section.size<8||word(p)!=0x31444652||word(p+4)>128)return 0;
 unsigned n=word(p+4);for(unsigned i=0;i<n;i++){
  if(section.size-pos<12)return 0;unsigned corners=word(p+pos),w=word(p+pos+4),h=word(p+pos+8);pos+=12;
  if(corners<3||corners>32||!w||w>1024||!h||h>1024)return 0;
  size_t bytes=(size_t)corners*40+(size_t)w*h*4;if(bytes>section.size-pos||!finite_doubles(p+pos,corners*5))return 0;
  widths[i]=w;heights[i]=h;if(corners_out)corners_out[i]=corners;pos+=bytes;
 }
 *base=pos;*count=n;return 1;
}
int nf_scene_world_surface(NFSceneSection section,unsigned index,NFSceneSection*out){
 if(!out)return 0;unsigned widths[128],heights[128],corners[128],count;size_t end;if(!world_layout(section,&end,&count,widths,heights,corners)||index>=count)return 0;size_t at=8;for(unsigned i=0;i<index;i++)at+=12+(size_t)corners[i]*40+(size_t)widths[i]*heights[i]*4;NFSceneSection result={section.data+at,12+(size_t)corners[index]*40+(size_t)widths[index]*heights[index]*4};*out=result;return 1;
}
static int world_metadata_modes(NFSceneSection section,unsigned index,const uint8_t**indices,size_t*size,unsigned*modes,NFWorldMetadata*bulk){
 unsigned widths[128],heights[128],corners[128],n;size_t pos;if(!world_layout(section,&pos,&n,widths,heights,corners))return -1;
 if(pos==section.size)return 0;const uint8_t*p=section.data;
 if(section.size-pos<8||word(p+pos)!=0x3149574e||word(p+pos+4)!=n)return -1;pos+=8;
 const uint8_t*chosen=NULL;size_t chosen_size=0,world_cursor=8;unsigned chosen_mode=0;
 for(unsigned i=0;i<n;i++){
  if(section.size-pos<8)return -1;unsigned mode=word(p+pos),bytes=word(p+pos+4);pos+=8;
  size_t pixels=(size_t)widths[i]*heights[i];
  size_t expected=pixels*(mode==3?17:mode==7?2:mode==8?34:1)+((mode==5||mode==6)?288u:(mode==9||mode==10)?344u:0u);
  if(mode>10||(mode==0&&bytes)||(mode&&bytes!=expected)||bytes>section.size-pos)return -1;
  if(mode==5||mode==6||mode==9||mode==10){
   NFRoadSourceAttributes raw;memcpy(&raw,p+pos+pixels+((mode==9||mode==10)?56:0),288);
   if(mode==9||mode==10){const uint8_t*camera=p+pos+pixels;uint32_t address=word(camera+4);if(word(camera)!=1||(address&3)||(uint64_t)address+48>0x100000000ull)return -1;}
   NFSceneSection surface={p+world_cursor,12+(size_t)corners[i]*40+(size_t)widths[i]*heights[i]*4};
   if(raw.affine!=(mode==6||mode==10)||!nf_scene_road_attributes_match(surface,&raw))return -1;
  }
  if(mode==2||mode==3){for(size_t k=0;k<bytes;k++)if(p[pos+k]>2)return -1;
   for(size_t k=0;k<pixels;k++){if(p[pos+k]==1)return -1;if(mode==3)for(unsigned level=1;level<17;level++)if((p[pos+k]==0)!=(p[pos+level*pixels+k]==0))return -1;}
  }
  if(mode==7||mode==8){
   unsigned planes=mode==8?17:1;size_t plane_bytes=pixels*planes;const uint8_t*states=p+pos,*output=states+plane_bytes;
   for(size_t k=0;k<plane_bytes;k++)if(states[k]>2||(states[k]==2)!=(output[k]!=0))return -1;
   for(size_t k=0;k<pixels;k++){if(states[k]==1)return -1;for(unsigned level=1;level<planes;level++)if((states[k]==0)!=(states[level*pixels+k]==0))return -1;}
  }
  if(i==index&&mode){chosen=p+pos;chosen_size=bytes;chosen_mode=mode;}pos+=bytes;
  world_cursor+=12+(size_t)corners[i]*40+(size_t)widths[i]*heights[i]*4;
  if(modes)modes[i]=mode;if(bulk)bulk[i]=(NFWorldMetadata){mode?p+pos-bytes:NULL,bytes,mode};
 }
 if(pos!=section.size)return -1;if(!chosen)return 0;
 if(indices)*indices=chosen;if(size)*size=chosen_size;return chosen_mode;
}
int nf_scene_world_metadata_all(NFSceneSection section,NFWorldMetadata*out,unsigned capacity,unsigned*count){
 if(!out||!count||!section.data||section.size<8)return 0;
 unsigned n=word(section.data+4);if(n>128||capacity<n)return 0;
 NFWorldMetadata items[128]={0};if(world_metadata_modes(section,UINT32_MAX,NULL,NULL,NULL,items)<0)return 0;
 memcpy(out,items,n*sizeof(*items));*count=n;return 1;
}
static int world_metadata(NFSceneSection section,unsigned index,const uint8_t**indices,size_t*size){return world_metadata_modes(section,index,indices,size,NULL,NULL);}
int nf_scene_world_indices(NFSceneSection section,unsigned index,const uint8_t**indices,size_t*size){
 if(!indices||!size)return 0;const uint8_t*p;size_t bytes;if(world_metadata(section,index,&p,&bytes)!=1)return 0;*indices=p;*size=bytes;return 1;
}
int nf_scene_world_road_mapping(NFSceneSection section,unsigned index,const uint8_t**indices,size_t*size,unsigned*affine){
 if(!indices||!size||!affine)return 0;const uint8_t*p;size_t bytes;int mode=world_metadata(section,index,&p,&bytes);
 if(mode!=1&&mode!=4&&mode!=5&&mode!=6&&mode!=9&&mode!=10)return 0;*indices=p;*size=bytes-((mode==9||mode==10)?344u:mode>=5?288u:0u);*affine=mode==4||mode==6||mode==10;return 1;
}
int nf_scene_world_wall_states(NFSceneSection section,unsigned index,const uint8_t**states,size_t*size,unsigned*planes){
 if(!states||!size||!planes)return 0;const uint8_t*p;size_t bytes;int mode=world_metadata(section,index,&p,&bytes);
 if(mode!=2&&mode!=3)return 0;*states=p;*size=bytes;*planes=mode==3?17:1;return 1;
}

static int world_attach(NFSceneSection section,unsigned index,const uint8_t*indices,size_t size,unsigned mode,void**out,size_t*out_size){
 unsigned widths[128],heights[128],n;size_t base;
 if(!out||!out_size||!indices||!world_layout(section,&base,&n,widths,heights,NULL)||index>=n||size!=(size_t)widths[index]*heights[index]*(mode==3?17:mode==7?2:mode==8?34:1)+((mode==5||mode==6)?288u:(mode==9||mode==10)?344u:0u)||world_metadata(section,UINT32_MAX,NULL,NULL)<0)return 0;
 const uint8_t*existing[128]={0};size_t lengths[128]={0};unsigned modes[128]={0};size_t total=base+8+n*8;if(total>64u*1024u*1024u)return 0;
 for(unsigned i=0;i<n;i++){
  if(i==index){existing[i]=indices;lengths[i]=size;modes[i]=mode;}else{int found=world_metadata(section,i,existing+i,lengths+i);modes[i]=found>0?(unsigned)found:0;}
  if(lengths[i]>64u*1024u*1024u-total)return 0;total+=lengths[i];
 }
 uint8_t*copy=malloc(total);if(!copy)return 0;memcpy(copy,section.data,base);put_word(copy+base,0x3149574e);put_word(copy+base+4,n);size_t pos=base+8;
 for(unsigned i=0;i<n;i++){put_word(copy+pos,modes[i]);put_word(copy+pos+4,(uint32_t)lengths[i]);pos+=8;if(lengths[i]){memcpy(copy+pos,existing[i],lengths[i]);pos+=lengths[i];}}
 if(world_metadata((NFSceneSection){copy,total},UINT32_MAX,NULL,NULL)<0){free(copy);return 0;}
 *out=copy;*out_size=total;return 1;
}
int nf_scene_world_attach_indices(NFSceneSection section,unsigned index,const uint8_t*indices,size_t size,void**out,size_t*out_size){return world_attach(section,index,indices,size,1,out,out_size);}
int nf_scene_world_attach_road_mapping(NFSceneSection section,unsigned index,const uint8_t*indices,size_t size,unsigned affine,void**out,size_t*out_size){if(affine>1)return 0;return world_attach(section,index,indices,size,affine?4:1,out,out_size);}
int nf_scene_world_road_attributes(NFSceneSection section,unsigned index,NFRoadSourceAttributes*out){
 if(!out)return 0;const uint8_t*p;size_t bytes;int mode=world_metadata(section,index,&p,&bytes);if(mode!=5&&mode!=6&&mode!=9&&mode!=10)return 0;
 NFRoadSourceAttributes result;memcpy(&result,p+bytes-288,288);memcpy(out,&result,288);return 1;
}
int nf_scene_world_attach_road_attributes(NFSceneSection section,unsigned index,const uint8_t*indices,size_t size,const NFRoadSourceAttributes*raw,void**out,size_t*out_size){
 if(!indices||!raw||!out||!out_size||raw->affine>1||size>1024u*1024u)return 0;
 uint8_t*payload=malloc(size+288);if(!payload)return 0;memcpy(payload,indices,size);memcpy(payload+size,raw,288);
 int ok=world_attach(section,index,payload,size+288,raw->affine?6:5,out,out_size);free(payload);return ok;
}
int nf_scene_world_attach_wall_states(NFSceneSection section,unsigned index,const uint8_t*states,size_t size,unsigned planes,void**out,size_t*out_size){if(planes!=1&&planes!=17)return 0;return world_attach(section,index,states,size,planes==17?3:2,out,out_size);}
int nf_scene_world_attach_wall_indices(NFSceneSection section,unsigned index,const uint8_t*states,const uint8_t*indices,size_t size,unsigned planes,void**out,size_t*out_size){
 if(!states||!indices||!size||size>17u*1024u*1024u||(planes!=1&&planes!=17)||!out||!out_size)return 0;
 uint8_t*paired=malloc(size*2);if(!paired)return 0;memcpy(paired,states,size);memcpy(paired+size,indices,size);
 int ok=world_attach(section,index,paired,size*2,planes==17?8:7,out,out_size);free(paired);return ok;
}
int nf_scene_world_wall_indices(NFSceneSection section,unsigned index,const uint8_t**states,const uint8_t**indices,size_t*size,unsigned*planes){
 if(!states||!indices||!size||!planes)return 0;const uint8_t*p;size_t bytes;int mode=world_metadata(section,index,&p,&bytes);
 if(mode!=7&&mode!=8)return 0;*states=p;*indices=p+bytes/2;*size=bytes/2;*planes=mode==8?17:1;return 1;
}
static unsigned section_models(NFSceneSection section){if(!section.data||section.size<8)return 0;if(word(section.data)==0x324d464e)return 1;if(word(section.data)!=0x314c4d4e)return 0;unsigned n=word(section.data+4);return n>=2&&n<=16?n:0;}
unsigned nf_scene_packet_model_count(const NFScenePacket*p){return p?section_models(p->section[0]):0;}
int nf_scene_packet_model(const NFScenePacket*p,unsigned index,NFSceneSection*out){
 if(!p||!out)return 0;NFSceneSection section=p->section[0];unsigned n=section_models(section);if(!n||index>=n)return 0;if(n==1){*out=section;return 1;}
 size_t end=8+n*8;if(end>section.size)return 0;NFSceneSection chosen={0};
 for(unsigned i=0;i<n;i++){size_t offset=word(section.data+8+i*8),size=word(section.data+12+i*8);if(offset%8||offset<end||offset>section.size||size>section.size-offset||size<160)return 0;if(i==index)chosen=(NFSceneSection){section.data+offset,size};end=offset+size;}
 if(end!=section.size)return 0;*out=chosen;return 1;
}
int nf_scene_packet_pair_model_indices(const NFScenePacket*older,const NFScenePacket*newer,unsigned*out,size_t capacity){
 if(!older||!newer||!out)return 0;
 unsigned models=nf_scene_packet_model_count(older),new_models=nf_scene_packet_model_count(newer);
 if(!models||models>16||models!=new_models||capacity<models)return 0;
 NFSceneSection ow=older->section[1],nw=newer->section[1],oi=older->section[4],ni=newer->section[4];
 if(!ow.data||!nw.data||ow.size<8||nw.size<8||word(ow.data)!=0x31444652||word(nw.data)!=0x31444652)return 0;
 unsigned world=word(ow.data+4),new_world=word(nw.data+4);
 if(world>128||new_world>128)return 0;
 size_t old_identity_bytes=8ull+(size_t)(world+models)*20,new_identity_bytes=8ull+(size_t)(new_world+models)*20;
 if(!oi.data||!ni.data||oi.size<old_identity_bytes||ni.size<new_identity_bytes||word(oi.data)!=0x3149464e||word(ni.data)!=0x3149464e||word(oi.data+4)!=world+models||word(ni.data+4)!=new_world+models)return 0;
 unsigned paired[16],used=0;
 const uint8_t*old_rows=oi.data+8+(size_t)world*20,*new_rows=ni.data+8+(size_t)new_world*20;
 for(unsigned i=0;i<models;i++){
  const uint8_t*identity=old_rows+(size_t)i*20;
  if(word(identity)!=3)return 0;
  unsigned found=models,matches=0;
  for(unsigned j=0;j<models;j++)if(word(new_rows+(size_t)j*20)==3&&!memcmp(identity,new_rows+(size_t)j*20,20)){found=j;matches++;}
  if(matches!=1||found>=models||(used&(1u<<found)))return 0;
  used|=1u<<found;paired[i]=found;
 }
 memcpy(out,paired,(size_t)models*sizeof(paired[0]));return 1;
}
/* Partial model membership changes retain the older draw set. Only unique
   complete source identities can supply newer object poses. */
int nf_scene_packet_pair_model_subset(const NFScenePacket*older,const NFScenePacket*newer,unsigned*out,size_t capacity,unsigned*matched_out){
 if(!older||!newer||!out||!matched_out)return 0;
 unsigned old_n=nf_scene_packet_model_count(older),new_n=nf_scene_packet_model_count(newer);
 if(!old_n||!new_n||old_n>16||new_n>16||capacity<old_n)return 0;
 NFSceneSection ow=older->section[1],nw=newer->section[1],oi=older->section[4],ni=newer->section[4];
 if(!ow.data||!nw.data||ow.size<8||nw.size<8||word(ow.data)!=0x31444652||word(nw.data)!=0x31444652)return 0;
 unsigned old_world=word(ow.data+4),new_world=word(nw.data+4);
 if(old_world>128||new_world>128)return 0;
 size_t old_bytes=8ull+(size_t)(old_world+old_n)*20,new_bytes=8ull+(size_t)(new_world+new_n)*20;
 if(!oi.data||!ni.data||oi.size<old_bytes||ni.size<new_bytes||word(oi.data)!=0x3149464e||word(ni.data)!=0x3149464e||word(oi.data+4)!=old_world+old_n||word(ni.data+4)!=new_world+new_n)return 0;
 const uint8_t*old_rows=oi.data+8+(size_t)old_world*20,*new_rows=ni.data+8+(size_t)new_world*20;
 for(unsigned i=0;i<old_n;i++)if(word(old_rows+i*20)!=3)return 0;
 for(unsigned i=0;i<new_n;i++)if(word(new_rows+i*20)!=3)return 0;
 unsigned map[16],matched=0;
 for(unsigned i=0;i<old_n;i++){
  const uint8_t*id=old_rows+i*20;unsigned old_hits=0,new_hits=0,found=UINT32_MAX;
  for(unsigned j=0;j<old_n;j++)old_hits+=!memcmp(id,old_rows+j*20,20);
  for(unsigned j=0;j<new_n;j++)if(!memcmp(id,new_rows+j*20,20)){found=j;new_hits++;}
  map[i]=old_hits==1&&new_hits==1?found:UINT32_MAX;if(map[i]!=UINT32_MAX)matched++;
 }
 memcpy(out,map,old_n*sizeof(*map));*matched_out=matched;return 1;
}
int nf_scene_packet_pair_world_indices(const NFScenePacket*older,const NFScenePacket*newer,unsigned*out,size_t capacity,unsigned*matched_out){
 if(!older||!newer||!matched_out)return 0;
 NFSceneSection ow=older->section[1],nw=newer->section[1],oi=older->section[4],ni=newer->section[4];
 unsigned old_models=nf_scene_packet_model_count(older),new_models=nf_scene_packet_model_count(newer);
 if(!old_models||!new_models||!ow.data||!nw.data||ow.size<8||nw.size<8||word(ow.data)!=0x31444652||word(nw.data)!=0x31444652)return 0;
 unsigned old_world=word(ow.data+4),new_world=word(nw.data+4);
 if(old_world>128||new_world>128||capacity<old_world||(old_world&&!out))return 0;
 size_t old_bytes=8ull+(size_t)(old_world+old_models)*20,new_bytes=8ull+(size_t)(new_world+new_models)*20;
 if(!oi.data||!ni.data||oi.size<old_bytes||ni.size<new_bytes||word(oi.data)!=0x3149464e||word(ni.data)!=0x3149464e||word(oi.data+4)!=old_world+old_models||word(ni.data+4)!=new_world+new_models)return 0;
 const uint8_t*old_rows=oi.data+8,*new_rows=ni.data+8;unsigned mapped[128],matched=0;
 for(unsigned i=0;i<old_world;i++){
  const uint8_t*identity=old_rows+(size_t)i*20;unsigned old_occurrences=0,new_occurrences=0,found=UINT32_MAX;
  unsigned kind=word(identity);if(kind!=1&&kind!=2)return 0;
  for(unsigned j=0;j<old_world;j++)if(!memcmp(identity,old_rows+(size_t)j*20,20))old_occurrences++;
  for(unsigned j=0;j<new_world;j++)if((word(new_rows+(size_t)j*20)==1||word(new_rows+(size_t)j*20)==2)&&!memcmp(identity,new_rows+(size_t)j*20,20)){found=j;new_occurrences++;}
  mapped[i]=old_occurrences==1&&new_occurrences==1?found:UINT32_MAX;
  if(mapped[i]!=UINT32_MAX)matched++;
 }
 if(old_world)memcpy(out,mapped,(size_t)old_world*sizeof(mapped[0]));*matched_out=matched;return 1;
}
void nf_scene_packet_free(void*data){free(data);}
int nf_scene_packet_build(const NFScenePacket*source,void**out,size_t*out_size){
 if(!source||!out||!out_size||source->section[0].size<4||source->page>1||source->end_refresh<source->begin_refresh)return 0;
 size_t size=96,offsets[5];
 for(unsigned i=0;i<5;i++){
  size=(size+7)&~(size_t)7;offsets[i]=size;
  if(!source->section[i].data||!source->section[i].size||source->section[i].size>64*1024*1024-size)return 0;
  size+=source->section[i].size;
 }
 uint8_t*data=calloc(1,size);if(!data)return 0;
 uint32_t header[8]={0x3150534e,word(source->section[0].data)==0x314c4d4e?2u:1u,(uint32_t)size,5,source->serial,source->begin_refresh,source->end_refresh,source->page};memcpy(data,header,32);
 for(unsigned i=0;i<5;i++){
  uint8_t*entry=data+32+i*12;put_word(entry,i+1);put_word(entry+4,(uint32_t)offsets[i]);put_word(entry+8,(uint32_t)source->section[i].size);
  memcpy(data+offsets[i],source->section[i].data,source->section[i].size);
 }
 NFScenePacket check;if(!nf_scene_packet_view(data,size,&check)){free(data);return 0;}
 *out=data;*out_size=size;return 1;
}
int nf_scene_packet_push(NFSnapshotStore*s,uint64_t epoch,const void*data,size_t size){
 NFScenePacket packet;if(!nf_scene_packet_view(data,size,&packet))return 0;
 return nf_snapshot_push(s,epoch,packet.serial,packet.end_refresh,data,size);
}
int nf_scene_packet_view(const void*data,size_t size,NFScenePacket*out){
 if(!data||!out||size<96||size>64*1024*1024)return 0;
 const uint8_t*p=data;if(word(p)!=0x3150534e||(word(p+4)!=1&&word(p+4)!=2)||word(p+8)!=size||word(p+12)!=5||word(p+28)>1||word(p+24)<word(p+20))return 0;
 NFScenePacket v={word(p+16),word(p+20),word(p+24),word(p+28),{{0}}};size_t end=96;
 for(unsigned i=0;i<5;i++){
  const uint8_t*d=p+32+i*12;size_t offset=word(d+4),length=word(d+8);
  if(word(d)!=i+1||offset%8||offset<end||offset>size||!length||length>size-offset)return 0;
  v.section[i]=(NFSceneSection){p+offset,length};end=offset+length;
 }if(end!=size)return 0;
 unsigned models=section_models(v.section[0]);if(!models||(word(p+4)==1)!=(models==1))return 0;
 for(unsigned i=0;i<models;i++){NFSceneSection model;if(!nf_scene_packet_model(&v,i,&model)||!validate_model(model.data,model.size))return 0;}
 const uint8_t*w=v.section[1].data;size_t ws=v.section[1].size;if(ws<8||word(w)!=0x31444652)return 0;
 unsigned count=word(w+4),widths[128],heights[128];if(count>128)return 0;size_t pos=8;
 for(unsigned i=0;i<count;i++){
  if(ws-pos<12)return 0;
  unsigned n=word(w+pos),width=word(w+pos+4),height=word(w+pos+8);pos+=12;
  if(n<3||n>32||!width||width>1024||!height||height>1024)return 0;
  uint64_t bytes=n*40ull+width*height*4ull;if(bytes>ws-pos||!finite_doubles(w+pos,n*5))return 0;
  widths[i]=width;heights[i]=height;pos+=(size_t)bytes;
 }unsigned metadata_modes[128]={0};if(world_metadata_modes(v.section[1],UINT32_MAX,NULL,NULL,metadata_modes,NULL)<0)return 0;
 const uint8_t*order=v.section[2].data;if(v.section[2].size!=8+(count+models)*4||word(order)!=0x314f464e||word(order+4)!=count+models)return 0;
 unsigned seen[144]={0};for(unsigned i=0;i<count+models;i++){unsigned index=word(order+8+i*4);if(index>=UINT32_MAX-15){unsigned model=UINT32_MAX-index;if(model>=models)return 0;index=count+model;}else if(index>=count)return 0;if(seen[index]++)return 0;}
 const uint8_t*l=v.section[3].data;size_t ls=v.section[3].size;if(ls<8||word(l)!=0x314c464e||word(l+4)!=count)return 0;pos=8;
 for(unsigned i=0;i<count;i++){
  if(ls-pos<4)return 0;
  unsigned enabled=word(l+pos);pos+=4;unsigned mode=metadata_modes[i];if(enabled>1||((mode==2||mode==4||mode==5||mode==6||mode==7||mode==9||mode==10)&&enabled)||((mode==3||mode==8)&&!enabled))return 0;if(!enabled)continue;
  if(ls-pos<16||word(l+pos)>15||word(l+pos+4)>15||word(l+pos+8)!=widths[i]||word(l+pos+12)!=heights[i])return 0;
  pos+=16;uint64_t bytes=widths[i]*heights[i]*64ull;if(bytes>ls-pos)return 0;pos+=(size_t)bytes;
 }if(ls-pos!=32768*4)return 0;
 const uint8_t*id=v.section[4].data;size_t ids_size=8+(count+models)*20;
 if((v.section[4].size!=ids_size&&v.section[4].size!=ids_size+16+count*8&&v.section[4].size!=ids_size+16+(count+models)*8)||word(id)!=0x3149464e||word(id+4)!=count+models)return 0;
 for(unsigned i=0;i<count+models;i++){unsigned kind=word(id+8+i*20);if(kind!=(i>=count?3u:1u)&&!(i<count&&kind==2))return 0;}
 for(unsigned i=0;i<count;i++){unsigned mode=metadata_modes[i],kind=word(id+8+i*20);if(((mode==2||mode==3||mode==7||mode==8)&&kind!=2)||((mode==1||mode==4||mode==5||mode==6)&&kind!=1))return 0;}
 if(v.section[4].size!=ids_size){
  const uint8_t*b=id+ids_size;double alpha;memcpy(&alpha,b+8,8);
  unsigned bounded=word(b+4);if((word(b)==0x3142464e?bounded!=count:word(b)==0x3242464e?bounded!=count+models:1)||v.section[4].size!=ids_size+16+bounded*8||!isfinite(alpha)||alpha<0||alpha>=1)return 0;
  for(unsigned i=0;i<bounded;i++){const uint8_t*r=b+16+i*8;if(half(r)>half(r+2)||half(r+2)>240||half(r+4)>half(r+6)||half(r+6)>160)return 0;}
 }
 *out=v;return 1;
}

int nf_scene_packet_bounds(const NFScenePacket*p,double*alpha,const uint8_t**bounds){
 if(!p||!alpha||!bounds)return 0;
 unsigned count=word(p->section[1].data+4);size_t offset=8+(count+nf_scene_packet_model_count(p))*20;
 if(p->section[4].size!=offset+16+count*8&&p->section[4].size!=offset+16+(count+nf_scene_packet_model_count(p))*8)return 0;
 const uint8_t*b=p->section[4].data+offset;memcpy(alpha,b+8,8);*bounds=b+16;return 1;
}
int nf_scene_packet_model_bounds(const NFScenePacket*p,const uint8_t**bounds){
 if(!p||!bounds)return 0;unsigned world=word(p->section[1].data+4),models=nf_scene_packet_model_count(p);size_t offset=8+(world+models)*20;
 if(p->section[4].size!=offset+16+(world+models)*8||word(p->section[4].data+offset)!=0x3242464e)return 0;
 *bounds=p->section[4].data+offset+16+world*8;return 1;
}
int nf_scene_packet_with_bounds(const void*data,size_t size,double alpha,const uint16_t*bounds,unsigned count,void**out,size_t*out_size){
 NFScenePacket p;if(!bounds||!out||!out_size||!nf_scene_packet_view(data,size,&p)||!isfinite(alpha)||alpha<0||alpha>=1)return 0;
 unsigned world=word(p.section[1].data+4),models=nf_scene_packet_model_count(&p);if(count!=world&&count!=world+models)return 0;
 size_t prefix=8+(world+models)*20,length=prefix+16+count*8;uint8_t*ids=malloc(length);if(!ids)return 0;
 memcpy(ids,p.section[4].data,prefix);put_word(ids+prefix,count==world?0x3142464e:0x3242464e);put_word(ids+prefix+4,count);memcpy(ids+prefix+8,&alpha,8);memcpy(ids+prefix+16,bounds,count*8);
 p.section[4]=(NFSceneSection){ids,length};int ok=nf_scene_packet_build(&p,out,out_size);free(ids);return ok;
}


int nf_scene_world_attach_road_camera(NFSceneSection section,unsigned index,const uint8_t*indices,size_t size,const NFRoadSourceAttributes*raw,const NFRoadCameraMetadata*camera,void**out,size_t*out_size){
 if(!indices||!raw||!camera||!out||!out_size||raw->affine>1||size>1024u*1024u)return 0;
 uint8_t*payload=malloc(size+344);if(!payload)return 0;
 memcpy(payload,indices,size);memcpy(payload+size,camera,56);memcpy(payload+size+56,raw,288);
 int ok=world_attach(section,index,payload,size+344,raw->affine?10:9,out,out_size);free(payload);return ok;
}
int nf_scene_world_road_camera(NFSceneSection section,unsigned index,NFRoadCameraMetadata*out){
 if(!out)return 0;const uint8_t*p;size_t bytes;int mode=world_metadata(section,index,&p,&bytes);if(mode!=9&&mode!=10)return 0;
 NFRoadCameraMetadata result;memcpy(&result,p+bytes-344,56);memcpy(out,&result,56);return 1;
}
