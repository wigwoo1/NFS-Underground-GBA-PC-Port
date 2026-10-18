#ifndef NF_ROAD_SPLIT_HUD_GPU_H
#define NF_ROAD_SPLIT_HUD_GPU_H
#include "owned_hud_gpu.h"
#include "ordered_scene_submission.h"
#include "stable_scene_submission.h"
static int render_road_split_hud(const void*old,size_t old_size,const void*newer,size_t new_size,const void*hud,size_t hud_size,const void*text,size_t text_size,unsigned cut,char**argv){
 NFRoadBundle a,b;NFHudSubmissionView submission;if(!nf_road_bundle_view(old,old_size,&a)||!nf_road_bundle_view(newer,new_size,&b)||!nf_hud_submission_view(&a,&b,hud,hud_size,text,text_size,cut,&submission))return 44;
 uint16_t saved[160][256];memcpy(saved,preview_display_palette,sizeof(saved));int saved_palette=preview_display_palette_valid,saved_zero=preview_zero_valid;
 for(unsigned y=0;y<160;y++)memcpy(preview_display_palette[y],(const uint8_t*)hud+y*sizeof(NFHudLayerRow)+32896,512);preview_display_palette_valid=preview_zero_valid=1;
 int saved_hud=preview_skip_diagnostic_hud;preview_skip_diagnostic_hud=1;int result=render_road_split(old,old_size,newer,new_size,cut,argv);preview_skip_diagnostic_hud=saved_hud;if(!result&&!owned_hud_gpu_draw(hud,hud_size,submission.indices,submission.coverage))result=46;
 memcpy(preview_display_palette,saved,sizeof(saved));preview_display_palette_valid=saved_palette;preview_zero_valid=saved_zero;return result;
}
static int render_ordered_scene_submission(const NFOrderedSceneSubmission*s,char**argv){if(!s)return 44;return render_road_split_hud(s->older,s->older_size,s->newer,s->newer_size,s->hud,s->hud_size,s->text,s->text_size,s->cut,argv);}
static int render_stable_scene_submission(const NFStableSceneSubmission*s,char**argv){
 NFHudSubmissionView view;if(!s||!nf_stable_scene_view(s->bundle,s->bundle_size,s->hud,s->hud_size,s->text,s->text_size,&s->proof,&view))return 44;
 uint16_t saved[160][256];memcpy(saved,preview_display_palette,sizeof(saved));int palette=preview_display_palette_valid,zero=preview_zero_valid;
 for(unsigned y=0;y<160;y++)memcpy(preview_display_palette[y],s->hud+y*sizeof(NFHudLayerRow)+32896,512);preview_display_palette_valid=preview_zero_valid=1;
 int saved_hud=preview_skip_diagnostic_hud;preview_skip_diagnostic_hud=1;int result=render_road_bundle(s->bundle,s->bundle_size,argv);preview_skip_diagnostic_hud=saved_hud;if(!result&&!owned_hud_gpu_draw(s->hud,s->hud_size,view.indices,view.coverage))result=46;
 memcpy(preview_display_palette,saved,sizeof(saved));preview_display_palette_valid=palette;preview_zero_valid=zero;return result;
}
#endif
