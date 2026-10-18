#ifndef NF_HUD_SUBMISSION_H
#define NF_HUD_SUBMISSION_H
#include "road_bundle.h"
#include "layer_snapshot.h"
typedef struct {const uint8_t*indices,*coverage,*hud;uint64_t epoch;uint32_t refresh,cut;} NFHudSubmissionView;
/* Whole input preflight, no borrowed pointer publication on failure. */
static int nf_hud_submission_view(const NFRoadBundle*a,const NFRoadBundle*b,const void*hud,size_t hud_size,const void*text,size_t text_size,unsigned cut,NFHudSubmissionView*out){
 if(!a||!b||!hud||!text||!out||!cut||cut>=160||hud_size!=160*sizeof(NFHudLayerRow)||text_size!=76832||a->ordered.epoch!=b->ordered.epoch||a->ordered.packet.serial>=b->ordered.packet.serial||a->ordered.packet.page==b->ordered.packet.page)return 0;
 uint32_t h[8];memcpy(h,text,32);uint64_t epoch=((uint64_t)h[3]<<32)|h[2];
 if(h[0]!=0x5854464e||h[1]!=1||!epoch||epoch!=b->ordered.epoch||h[4]!=b->ordered.packet.end_refresh||h[5]!=240||h[6]!=160||h[7]!=38400)return 0;
 const uint8_t*coverage=(const uint8_t*)text+38432;for(unsigned i=0;i<38400;i++)if(coverage[i]>1)return 0;
 for(unsigned y=0;y<160;y++){NFHudLayerRow row;memcpy(&row,(const uint8_t*)hud+y*sizeof(row),sizeof(row));unsigned display=row.registers[0]|((unsigned)row.registers[1]<<8),page=(display>>4)&1;
 if(row.refresh!=h[4]||row.row!=y||(display&0x8080)||(display&7)!=4||page!=(y<cut?a->ordered.packet.page:b->ordered.packet.page))return 0;}
 NFHudSubmissionView v={(const uint8_t*)text+32,coverage,hud,epoch,h[4],cut};*out=v;return 1;
}
#endif
