#include "render_handoff.h"
#define NF_PACKET_NO_MAIN
#ifdef NF_TEST_ENDPOINT_BOUNDS
#include "scene_packet.h"
static void endpoint_select(const NFScenePacket*);
static void endpoint_clip(int);
static void endpoint_model_clip(int);
static int endpoint_road(unsigned,double*,double*,double*,double*);
#define NF_DIAGNOSTIC_PACKET_SELECT endpoint_select
#define NF_DIAGNOSTIC_SURFACE_CLIP endpoint_clip
#define NF_DIAGNOSTIC_MODEL_CLIP endpoint_model_clip
#define NF_DIAGNOSTIC_ROAD_BOUNDS endpoint_road
#endif
#include "packet_preview.c"
#ifdef NF_TEST_ENDPOINT_BOUNDS
#include "endpoint_surface_bounds.h"
#endif
#include "road_split_hud_gpu.h"
#include "road_motion_clone.h"
static uint8_t*motion_hud,*motion_text;static size_t motion_hud_size;
static int motion_render(const void*p,size_t n,char**args){int rc=render_road_bundle(p,n,args);if(!rc&&motion_hud&&!owned_hud_gpu_draw(motion_hud,motion_hud_size,motion_text+32,motion_text+38432))return 46;return rc;}
static void*load(const char*path,size_t*size){FILE*f=fopen(path,"rb");if(!f)return NULL;fseek(f,0,SEEK_END);*size=ftell(f);rewind(f);void*p=malloc(*size);if(!p||fread(p,1,*size,f)!=*size){free(p);p=NULL;}fclose(f);return p;}
int main(int argc,char**argv){if(argc!=4&&argc!=7)return 1;size_t an,bn,pn;void*a=load(argv[1],&an),*b=load(argv[2],&bn),*palette=load(argv[3],&pn);if(!a||!b||!palette||pn!=81920)return 2;if(argc==7){size_t hs,ts;void*h=load(argv[4],&hs),*t=load(argv[5],&ts);NFRoadBundle av,bv;NFHudSubmissionView view;if(!h||!t||!nf_road_bundle_view(a,an,&av)||!nf_road_bundle_view(b,bn,&bv)||!nf_hud_submission_view(&av,&bv,h,hs,t,ts,(unsigned)atoi(argv[6]),&view))return 14;motion_hud=malloc(hs);motion_text=malloc(ts);if(!motion_hud||!motion_text)return 15;memcpy(motion_hud,h,hs);memcpy(motion_text,t,ts);motion_hud_size=hs;free(h);free(t);}memcpy(preview_display_palette,palette,pn);preview_zero_valid=preview_display_palette_valid=preview_measure_only=preview_keep_context=preview_skip_diagnostic_hud=1;_putenv("NF_PREVIEW_PHASE=0");char*args[]={argv[0],"unused","unused","unused"};size_t bytes=3840u*2160u*4;unsigned char*old=malloc(bytes),*newer=malloc(bytes),*pixels=malloc(bytes),*repeat=malloc(bytes);if(!old||!newer||!pixels||!repeat)return 3;
 if(motion_render(a,an,args))return 4;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,old);if(motion_render(b,bn,args))return 5;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,newer);
 void*owners[5]={0};size_t sizes[5];for(unsigned phase=0;phase<=4;phase++)if(!nf_road_motion_clone(a,an,b,bn,phase/4.,owners+phase,sizes+phase))return 6;free(a);free(b);free(palette);
 for(unsigned phase=0;phase<=4;phase++){if(motion_render(owners[phase],sizes[phase],args))return 7;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);if((phase==0&&memcmp(pixels,old,bytes))||(phase==4&&memcmp(pixels,newer,bytes)))return 8;unsigned changes=0;for(size_t i=0;i<bytes;i+=4)if(memcmp(pixels+i,old+i,4))changes++;if(phase>0&&phase<4&&!changes)return 9;if(motion_render(owners[phase],sizes[phase],args))return 10;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,repeat);if(memcmp(pixels,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 11;if(phase==2){preview_shutdown();if(motion_render(owners[phase],sizes[phase],args))return 12;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,repeat);if(memcmp(pixels,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 13;printf("midpoint_context_reopen_exact=8294400\n");}printf("phase=%u alpha=%.2f changed_pixels=%u repeat_exact=1\n",phase,phase/4.,changes);free(owners[phase]);}
 preview_shutdown();printf("owned_hud_text=%u original_display_rows=160\n",motion_hud!=NULL);free(motion_hud);free(motion_text);free(old);free(newer);free(pixels);free(repeat);printf("PASS diagnostic owned motion GPU endpoints_RGBA_exact=8294400 source_free=1 phases=5 no_fullscene60fps_claim=1\n");return 0;}
