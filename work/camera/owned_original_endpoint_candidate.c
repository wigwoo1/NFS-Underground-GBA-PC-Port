/* Diagnostic only: original retained geometry, no interpolated pose/mask overrides. */
#include "owned_gpu_hud_borrowed_rows_candidate.c"
__declspec(dllexport) int nf_original_endpoint_callback(void*opaque){
 if(!opaque)return 37;NFOwnedDrawContext*c=opaque;
 if(c->camera||c->models||c->bounds||!c->frame||c->bytes<40||!c->lower||!c->upper||c->skycount!=15136||!isfinite(c->weight)||c->weight<0||c->weight>=1||sky_lower||anchor_raw_a||source_face_mask)return 37;
 if(gpu_owner!=GetCurrentThreadId())return 31;
 size_t count=c->skycount;sky_lower=c->lower;sky_upper=c->upper;sky_weight=c->weight;c->skycount=0;
 int result=nf_owned_gpu_draw_context_callback(c);
 c->skycount=count;sky_lower=sky_upper=NULL;sky_weight=0;return result;
}
