#include "object_callback.h"
#include <string.h>
static uint16_t h(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static uint32_t w(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static void put(uint8_t*p,uint16_t v){memcpy(p,&v,2);}
int nf_object_damage(uint8_t object[164],unsigned*changed){
 if(!object||!changed)return 0;
 int16_t delta=(int16_t)h(object+96);uint16_t result=(uint16_t)(h(object+108)+delta);
 put(object+108,result);put(object+96,0);if((int16_t)result<0)put(object+74,2);*changed=delta!=0;return 1;
}
static int ground(const uint8_t state[256],uint8_t*object,NFVisibilityRead read,void*user){
 int32_t height;int32_t x=(int32_t)w(object+12),z=(int32_t)w(object+20);
 /* Defined arithmetic shift for original signed Q8 world coordinates. */
 x=(int32_t)((uint32_t)x>>8)|((x<0)?(int32_t)0xff000000u:0);z=(int32_t)((uint32_t)z>>8)|((z<0)?(int32_t)0xff000000u:0);
 if(!nf_object_ground_height(state,h(object+120),x,z,read,user,&height))return 0;
 memcpy(object+16,&height,4);return 1;
}
int nf_object_callback12(const uint8_t state[256],uint8_t object[164],NFVisibilityRead read,void*user,NFObjectProjection project,void*project_user,unsigned*event){
 if(!state||!object||!read||!project||!event)return 0;
 uint8_t staged[164];memcpy(staged,object,164);unsigned sound=0,mode=h(staged+74),changed;
 if(mode==0){if(!ground(state,staged,read,user))return 0;staged[136]=255;put(staged+74,1);if(!ground(state,staged,read,user))return 0;put(staged+50,(uint16_t)((w(staged+44)>>8)&16383));}
 else if(mode==1){if(!ground(state,staged,read,user))return 0;put(staged+50,(uint16_t)((w(staged+44)>>8)&16383));if(!nf_object_damage(staged,&changed))return 0;if(changed){put(staged+74,3);sound=10;}}
 else if(mode==3)put(staged+74,1);
 if(!project(project_user,state,staged))return 0;
 memcpy(object,staged,164);*event=sound;return 1;
}
