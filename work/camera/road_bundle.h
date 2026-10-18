#ifndef NF_ROAD_BUNDLE_H
#define NF_ROAD_BUNDLE_H
#include "ordered_bundle.h"
#include "road_asset.h"
typedef struct {NFOrderedBundle ordered;const uint8_t*data,*directory,*baseline;size_t baseline_size;unsigned count;size_t size;} NFRoadBundle;
/* Canonical contiguous layout and increasing original event links. Atomic. */
static int nf_road_bundle_view(const void*data,size_t size,NFRoadBundle*out){
 if(!data||!out||size<32||size>64*1024*1024)return 0;const uint8_t*p=data;uint32_t h[8];memcpy(h,p,32);
 if(h[0]!=0x4252464e||(h[1]!=1&&h[1]!=2)||h[3]>144||h[4]!=32||h[5]!=32+h[3]*16+(h[1]==2?1960:0)||h[7]!=size||h[5]>size||h[6]>size-h[5])return 0;
 NFRoadBundle v;if(!nf_ordered_bundle_view(p+h[5],h[6],&v.ordered)||v.ordered.packet.serial!=h[2])return 0;
 v.baseline=NULL;v.baseline_size=0;
 if(h[1]==2){uint32_t kind,page,at;const uint8_t*indices;size_t bytes;v.baseline=p+32+h[3]*16;v.baseline_size=1960;
 if(!nf_indexed_operation_view(v.baseline,1960,&kind,&page,&at,&indices,&bytes)||kind!=2||page!=v.ordered.packet.page||at!=3840||bytes!=1920||nf_bundle_word(v.baseline+8))return 0;}
 size_t offset=h[5]+h[6];unsigned cursor=0;
 for(unsigned i=0;i<h[3];i++){uint32_t e[4];memcpy(e,p+32+i*16,16);NFRoadAssetView asset;
 if(e[2]!=offset||e[3]>size-offset||!nf_road_asset_view(p+offset,e[3],&asset)||asset.header[2]!=h[2]||asset.header[3]!=e[0]||asset.header[4]!=e[1])return 0;
 int found=0;while(cursor<v.ordered.event_count){NFOrderedSceneEvent event;memcpy(&event,v.ordered.events+cursor++*32,32);
 if(event.type==3&&event.kind==1&&event.pass==e[0]&&event.ordinal==e[1]){found=1;break;}}
 if(!found)return 0;offset+=e[3];
 }if(offset!=size)return 0;
 v.data=p;v.directory=p+32;v.count=h[3];v.size=size;*out=v;return 1;
}
#endif
