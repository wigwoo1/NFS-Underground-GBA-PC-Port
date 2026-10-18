#ifndef NF_ORDERED_SCENE_SUBMISSION_H
#define NF_ORDERED_SCENE_SUBMISSION_H
#include <stdlib.h>
#include "hud_submission.h"
typedef struct {const uint8_t*older,*newer,*hud,*text;size_t older_size,newer_size,hud_size,text_size;uint64_t epoch;unsigned refresh,cut;uint8_t storage[];} NFOrderedSceneSubmission;
/* One exclusive allocation owns every byte. Publish only after owned copy
   validation. Caller/worker transfer this sole owner, never borrowed history. */
static int nf_ordered_scene_submission_create(const void*older,size_t older_size,const void*newer,size_t newer_size,const void*hud,size_t hud_size,const void*text,size_t text_size,unsigned cut,NFOrderedSceneSubmission**out){
 if(!out||older_size>64*1024*1024||newer_size>64*1024*1024||hud_size!=160*sizeof(NFHudLayerRow)||text_size!=76832)return 0;
 NFRoadBundle a,b;NFHudSubmissionView view;if(!nf_road_bundle_view(older,older_size,&a)||!nf_road_bundle_view(newer,newer_size,&b)||!nf_hud_submission_view(&a,&b,hud,hud_size,text,text_size,cut,&view))return 0;
 size_t total=older_size+newer_size+hud_size+text_size;if(total>128*1024*1024)return 0;NFOrderedSceneSubmission*s=malloc(sizeof(*s)+total);if(!s)return 0;
 s->older=s->storage;s->newer=s->older+older_size;s->hud=s->newer+newer_size;s->text=s->hud+hud_size;
 s->older_size=older_size;s->newer_size=newer_size;s->hud_size=hud_size;s->text_size=text_size;s->epoch=view.epoch;s->refresh=view.refresh;s->cut=cut;
 memcpy((void*)s->older,older,older_size);memcpy((void*)s->newer,newer,newer_size);memcpy((void*)s->hud,hud,hud_size);memcpy((void*)s->text,text,text_size);
 if(!nf_road_bundle_view(s->older,s->older_size,&a)||!nf_road_bundle_view(s->newer,s->newer_size,&b)||!nf_hud_submission_view(&a,&b,s->hud,s->hud_size,s->text,s->text_size,cut,&view)){free(s);return 0;}*out=s;return 1;
}
static void nf_ordered_scene_submission_destroy(NFOrderedSceneSubmission*s){free(s);}
#endif
