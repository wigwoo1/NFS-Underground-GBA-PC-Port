
#ifndef NF_LIVE_HUD_ADAPTER_H
#define NF_LIVE_HUD_ADAPTER_H
#include "layer_snapshot.h"
/* One owner thread; deep copies of one epoch/refresh, never raster scene pixels. */
static int hud_preview;static uint64_t hud_epoch;static unsigned hud_refresh,hud_drawn,hud_failed;
static NFHudLayerRow live_hud_rows[160];
static uint8_t live_hud_text[38400],live_hud_coverage[38400];
static void* owned_submission;
static unsigned live_hud_select_misses,live_hud_text_missing,live_hud_selected;
static int(*live_hud_row_fn)(uint64_t,unsigned,unsigned,void*,unsigned);
static int(*live_hud_text_fn)(uint64_t,unsigned,unsigned,void*,void*,unsigned);
static int layer_read(uint64_t epoch,unsigned refresh,unsigned row,void*out,unsigned bytes){
 if(epoch!=hud_epoch||refresh!=hud_refresh||row>=160||bytes!=sizeof(NFHudLayerRow))return 0;
 memcpy(out,live_hud_rows+row,bytes);return 1;
}
static int nf_submission_text_row(void*submission,uint64_t epoch,unsigned refresh,unsigned row,uint8_t*indices,uint8_t*coverage){
 if(!submission||epoch!=hud_epoch||refresh!=hud_refresh||row>=160)return 0;
 memcpy(indices,live_hud_text+row*240,240);memcpy(coverage,live_hud_coverage+row*240,240);return 1;
}
#include "live_hud_gpu.h"
static int live_hud_enable(HMODULE bridge){
 if(!getenv("NF_LIVE_HUD"))return 1;
 int(*queue_enable)(unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_enable");
 int(*text_enable)(unsigned)=(void*)GetProcAddress(bridge,"nf_bitmap_text_enable");
 unsigned(*row_size)(void)=(void*)GetProcAddress(bridge,"nf_layer_hud_row_size");
 live_hud_row_fn=(void*)GetProcAddress(bridge,"nf_layer_queue_hud_row");
 live_hud_text_fn=(void*)GetProcAddress(bridge,"nf_layer_queue_text_row");
 if(!queue_enable||!text_enable||!row_size||!live_hud_row_fn||!live_hud_text_fn||row_size()!=sizeof(NFHudLayerRow))return 0;
 if(!queue_enable(1)||!text_enable(1))return 0;
 hud_preview=1;return 1;
}
static int live_hud_select(uint64_t epoch,unsigned refresh){
 if(!hud_preview)return 1;
 if(live_hud_selected&&hud_epoch==epoch&&hud_refresh==refresh)return 1;
 for(unsigned y=0;y<160;y++)if(!live_hud_row_fn(epoch,refresh,y,live_hud_rows+y,sizeof(NFHudLayerRow))||live_hud_rows[y].refresh!=refresh||live_hud_rows[y].row!=y){live_hud_select_misses++;return 0;}
 /* Text provenance is independent; record missing text instead of using raster pixels. */
 int has_text=live_hud_text_fn(epoch,refresh,0,live_hud_text,live_hud_coverage,240);
 if(has_text){
  for(unsigned y=1;y<160;y++)if(!live_hud_text_fn(epoch,refresh,y,live_hud_text+y*240,live_hud_coverage+y*240,240)){live_hud_select_misses++;return 0;}
 }else live_hud_text_missing++;
 hud_epoch=epoch;hud_refresh=refresh;owned_submission=has_text?live_hud_text:NULL;live_hud_selected++;return 1;
}
static int live_hud_draw(void){
 if(!hud_preview)return 1;
 glPushAttrib(GL_VIEWPORT_BIT);glViewport(0,0,3840,2160);
 int ok=endpoint_hud();glPopAttrib();return ok&&glGetError()==GL_NO_ERROR;
}
static void live_hud_close(void){
 if(hud_background)glDeleteTextures(1,&hud_background);
 if(hud_program){void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteProgram");if(remove)remove(hud_program);if(obj_affine_program==hud_program)obj_affine_program=0;}
 hud_background=hud_program=0;hud_preview=0;
}
#endif
