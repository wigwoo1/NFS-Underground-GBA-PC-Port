#ifndef NF_STABLE_SCENE_SUBMISSION_H
#define NF_STABLE_SCENE_SUBMISSION_H
#include "ordered_scene_submission.h"
#include "hud_row_pool.h"
/* Producer provenance from the same uninterrupted observer epoch. A reset or
   unobserved mutation invalidates proof; equal values alone cannot detect it. */
typedef struct {uint64_t epoch,completion_generation,display_generation;uint32_t serial,completion_refresh,display_refresh,page;} NFPagePersistenceProof;
typedef struct {NFPagePersistenceProof proof;const uint8_t*bundle,*hud,*text;size_t bundle_size,hud_size,text_size;uint8_t storage[];} NFStableSceneSubmission;
/* Internal borrowed view must come from canonical validation in this call scope. */
static int nf_stable_scene_view_validated(const NFRoadBundle*b,const void*hud,size_t hud_size,const void*text,size_t text_size,const NFPagePersistenceProof*proof,NFHudSubmissionView*out){
 if(!b||!proof||!out||!hud||!text||hud_size!=160*sizeof(NFHudLayerRow)||text_size!=76832||!proof->epoch||proof->page>1||proof->completion_generation!=proof->display_generation||proof->display_refresh<proof->completion_refresh)return 0;
 if(b->ordered.epoch!=proof->epoch||b->ordered.packet.serial!=proof->serial||b->ordered.packet.end_refresh!=proof->completion_refresh||b->ordered.packet.page!=proof->page)return 0;
 uint32_t h[8];memcpy(h,text,32);if(h[0]!=0x5854464e||h[1]!=1||(((uint64_t)h[3]<<32)|h[2])!=proof->epoch||h[4]!=proof->display_refresh||h[5]!=240||h[6]!=160||h[7]!=38400)return 0;
 const uint8_t*coverage=(const uint8_t*)text+38432;for(unsigned i=0;i<38400;i++)if(coverage[i]>1)return 0;
 for(unsigned y=0;y<160;y++){NFHudLayerRow row;memcpy(&row,(const uint8_t*)hud+y*sizeof(row),sizeof(row));unsigned display=row.registers[0]|((unsigned)row.registers[1]<<8);if(row.refresh!=proof->display_refresh||row.row!=y||(display&0x8080)||(display&7)!=4||((display>>4)&1)!=proof->page)return 0;}
 NFHudSubmissionView view={(const uint8_t*)text+32,coverage,hud,proof->epoch,proof->display_refresh,160};*out=view;return 1;
}
static int nf_stable_scene_pool_view_validated(const NFRoadBundle*b,const NFHudRowPool*pool,size_t pool_size,const void*text,size_t text_size,const NFPagePersistenceProof*proof,NFHudSubmissionView*out){
 if(!b||!proof||!out||!pool||!text||!nf_hud_pool_valid(pool,pool_size,proof->epoch)||text_size!=76832||!proof->epoch||proof->page>1||proof->completion_generation!=proof->display_generation||proof->display_refresh<proof->completion_refresh)return 0;
 if(b->ordered.epoch!=proof->epoch||b->ordered.packet.serial!=proof->serial||b->ordered.packet.end_refresh!=proof->completion_refresh||b->ordered.packet.page!=proof->page)return 0;
 uint32_t h[8];memcpy(h,text,32);if(h[0]!=0x5854464e||h[1]!=1||(((uint64_t)h[3]<<32)|h[2])!=proof->epoch||h[4]!=proof->display_refresh||h[5]!=240||h[6]!=160||h[7]!=38400)return 0;
 const uint8_t*coverage=(const uint8_t*)text+38432;for(unsigned i=0;i<38400;i++)if(coverage[i]>1)return 0;
 for(unsigned y=0;y<160;y++){NFHardwareLayerHeader row=pool->headers[y];unsigned display=row.registers[0]|((unsigned)row.registers[1]<<8);if(row.refresh!=proof->display_refresh||row.row!=y||(display&0x8080)||(display&7)!=4||((display>>4)&1)!=proof->page)return 0;}
 NFHudSubmissionView view={(const uint8_t*)text+32,coverage,NULL,proof->epoch,proof->display_refresh,160};*out=view;return 1;
}
static int nf_stable_scene_view(const void*bundle,size_t bundle_size,const void*hud,size_t hud_size,const void*text,size_t text_size,const NFPagePersistenceProof*proof,NFHudSubmissionView*out){NFRoadBundle b;return nf_road_bundle_view(bundle,bundle_size,&b)&&nf_stable_scene_view_validated(&b,hud,hud_size,text,text_size,proof,out);}
static int nf_stable_scene_create(const void*bundle,size_t bundle_size,const void*hud,size_t hud_size,const void*text,size_t text_size,const NFPagePersistenceProof*proof,NFStableSceneSubmission**out){
 NFHudSubmissionView view;if(!out||bundle_size>64*1024*1024||!nf_stable_scene_view(bundle,bundle_size,hud,hud_size,text,text_size,proof,&view))return 0;
 size_t bytes=bundle_size+hud_size+text_size;NFStableSceneSubmission*s=malloc(sizeof(*s)+bytes);if(!s)return 0;s->proof=*proof;s->bundle=s->storage;s->hud=s->bundle+bundle_size;s->text=s->hud+hud_size;s->bundle_size=bundle_size;s->hud_size=hud_size;s->text_size=text_size;memcpy((void*)s->bundle,bundle,bundle_size);memcpy((void*)s->hud,hud,hud_size);memcpy((void*)s->text,text,text_size);
 if(!nf_stable_scene_view(s->bundle,s->bundle_size,s->hud,s->hud_size,s->text,s->text_size,&s->proof,&view)){free(s);return 0;}*out=s;return 1;
}
static void nf_stable_scene_destroy(NFStableSceneSubmission*s){free(s);}
#endif
