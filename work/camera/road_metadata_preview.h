#ifndef NF_ROAD_METADATA_PREVIEW_H
#define NF_ROAD_METADATA_PREVIEW_H
#include "scene_packet.h"
#include <string.h>
static int nf_preview_road_metadata(const NFWorldMetadata*m,NFRoadSourceAttributes*attrs,NFRoadCameraMetadata*camera,unsigned*present,unsigned*affine){
 if(!m||!attrs||!camera||!present||!affine||(m->mode!=5&&m->mode!=6&&m->mode!=9&&m->mode!=10))return 0;
 unsigned has=m->mode==9||m->mode==10;size_t tail=has?344:288;if(!m->data||m->size<tail)return 0;
 NFRoadSourceAttributes a;NFRoadCameraMetadata c={0};memcpy(&a,m->data+m->size-288,288);
 if(has){memcpy(&c,m->data+m->size-344,56);if(c.version!=1||(c.address&3)||(uint64_t)c.address+48>0x100000000ull)return 0;}
 memcpy(attrs,&a,288);memcpy(camera,&c,56);*present=has;*affine=m->mode==6||m->mode==10;return 1;
}
#endif
