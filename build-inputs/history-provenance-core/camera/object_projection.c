#include "object_projection.h"
#include "object_callback.h"
#include <string.h>
static uint16_t h(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static uint32_t w(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint32_t shift14(uint32_t v){return (uint32_t)((int32_t)v>>14);}
static void multiply(const uint32_t*a,const uint32_t*b,uint32_t*out){
 for(unsigned r=0;r<3;r++)for(unsigned c=0;c<3;c++)out[r*3+c]=shift14(a[r*3]*b[c]+a[r*3+1]*b[3+c]+a[r*3+2]*b[6+c]);
}
static int sine(NFVisibilityRead read,void*user,int angle,int32_t*out){
 unsigned phase=(unsigned)angle&16383u,index=phase&8191u;int16_t value;
 if(!read(user,0x08623700u+index*2u,&value,2))return 0;
 *out=phase>=8192u?-(int32_t)value:value;return 1;
}
int nf_object_projection_matrix(const uint32_t camera[12],const uint8_t object[164],uint32_t output[12],NFVisibilityRead read,void*user){
 if(!camera||!object||!output||!read)return 0;
 uint32_t x=(uint32_t)((int32_t)w(object+12)>>8)+camera[9],z=(uint32_t)((int32_t)w(object+20)>>8)+camera[11];
 uint32_t depth=shift14(camera[2]*x+camera[8]*z);unsigned flags=h(object+10);
 if(!(flags&2)&&(int32_t)depth>3500)return 1;
 uint32_t staged[12];memcpy(staged,output,48);
 uint32_t special=0;
 if((flags&32)&&!read(user,0x03006768u,&special,4))return 0;
 if((flags&32)&&special){
  uint32_t external[9],address=w(object+140);if(address>UINT32_MAX-356u||!read(user,address+320,external,36))return 0;
  for(unsigned i=0;i<9;i++)external[i]<<=2;
  multiply(external,camera,staged);
 }else{
  int32_t sx,cx,sy,cy;
  if(!sine(read,user,(int16_t)h(object+48),&sx)||!sine(read,user,(int16_t)h(object+48)+4096,&cx)||!sine(read,user,(int16_t)h(object+50),&sy)||!sine(read,user,(int16_t)h(object+50)+4096,&cy))return 0;
  uint32_t rx[9]={16384,0,0,0,(uint32_t)cx,(uint32_t)sx,0,(uint32_t)-sx,(uint32_t)cx};
  uint32_t ry[9]={(uint32_t)cy,0,(uint32_t)-sy,0,16384,0,(uint32_t)sy,0,(uint32_t)cy},temp[9];
  multiply(rx,camera,temp);multiply(temp,ry,staged);
 }
 staged[9]=shift14(camera[0]*x+camera[6]*z);staged[10]=(uint32_t)((int32_t)w(object+16)>>8)+camera[10];staged[11]=depth;
 memcpy(output,staged,48);return 1;
}
int nf_object_projection_slot(const uint8_t state[256],uint8_t object[164],uint32_t*counter,uint8_t scratch[64*48],NFVisibilityRead read,void*read_user,NFObjectMatrixBuilder builder,void*builder_user){
 if(!state||!object||!counter||!scratch||!read)return 0;
 uint8_t staged[164];memcpy(staged,object,164);uint32_t next=*counter,matrix[12];unsigned slot=255;
 if((int16_t)h(staged+54)&&(h(staged+10)&4)){
  next++;if((int32_t)next<=63)slot=*counter&255u;
  staged[136]=(uint8_t)slot;
  if(slot!=255){if(slot>=64||!builder)return 0;uint32_t camera[12];memcpy(matrix,scratch+slot*48,48);if(!read(read_user,w(state+84),camera,48)||!builder(builder_user,camera,staged,matrix))return 0;}
 }
 staged[136]=(uint8_t)slot;uint16_t flags=h(staged+10)&(uint16_t)~4u;memcpy(staged+10,&flags,2);
 if(slot!=255)memcpy(scratch+slot*48,matrix,48);
 memcpy(object,staged,164);*counter=next;return 1;
}
typedef struct {uint32_t counter;uint8_t scratch[64*48];NFVisibilityRead read;void*user;} OwnedProjection;
static int owned_matrix(void*ctx,const uint32_t camera[12],const uint8_t object[164],uint32_t out[12]){
 OwnedProjection*p=ctx;return nf_object_projection_matrix(camera,object,out,p->read,p->user);
}
static int owned_projection(void*ctx,const uint8_t state[256],uint8_t object[164]){
 OwnedProjection*p=ctx;return nf_object_projection_slot(state,object,&p->counter,p->scratch,p->read,p->user,owned_matrix,p);
}
int nf_object_callback12_owned(const uint8_t state[256],uint8_t object[164],uint32_t*counter,uint8_t scratch[64*48],NFVisibilityRead read,void*user,unsigned*event){
 if(!state||!object||!counter||!scratch||!read||!event)return 0;
 OwnedProjection p;p.counter=*counter;p.read=read;p.user=user;memcpy(p.scratch,scratch,sizeof(p.scratch));
 if(!nf_object_callback12(state,object,read,user,owned_projection,&p,event))return 0;
 *counter=p.counter;memcpy(scratch,p.scratch,sizeof(p.scratch));return 1;
}
