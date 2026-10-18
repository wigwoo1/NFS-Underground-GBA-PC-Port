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
#include "live_rgb_reference.h"
static void*load(const char*path,size_t*size){FILE*f=fopen(path,"rb");if(!f)return NULL;fseek(f,0,SEEK_END);*size=ftell(f);rewind(f);void*p=malloc(*size);if(!p||fread(p,1,*size,f)!=*size){free(p);p=NULL;}fclose(f);return p;}
int main(int argc,char**argv){if(argc!=5&&argc!=6)return 1;size_t bn,hn,tn,pn;void*b=load(argv[1],&bn),*h=load(argv[2],&hn),*t=load(argv[3],&tn);NFPagePersistenceProof*p=load(argv[4],&pn);if(!b||!h||!t||!p||pn!=sizeof(*p))return 2;NFHudSubmissionView view;if(!nf_stable_scene_view(b,bn,h,hn,t,tn,p,&view))return 3;
 preview_zero_valid=preview_display_palette_valid=preview_measure_only=preview_keep_context=1;_putenv("NF_PREVIEW_PHASE=0");for(unsigned y=0;y<160;y++)memcpy(preview_display_palette[y],(uint8_t*)h+y*sizeof(NFHudLayerRow)+32896,512);char*args[]={argv[0],"unused","unused","unused"};size_t bytes=3840u*2160u*4;void*reference=malloc(bytes),*result=malloc(bytes);if(!reference||!result)return 4;
 if(render_road_bundle(b,bn,args)||!owned_hud_gpu_draw(h,hn,view.indices,view.coverage))return 5;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,reference);
 if(!nf_live_rgb_reference(reference,3840u*2160u))return 16;
 NFStableSceneSubmission*owner=NULL;if(!nf_stable_scene_create(b,bn,h,hn,t,tn,p,&owner))return 6;NFTimelineSample time={p->epoch,p->serial,p->serial,0,p->display_refresh};NFSubmissionSchedule schedule={100,200,3000,2};NFRenderSubmission*frame=(void*)123;time.target++;if(nf_render_submission_stable(&owner,&time,&schedule,&frame)||!owner||frame!=(void*)123)return 7;time.target--;frame=NULL;if(!nf_render_submission_stable(&owner,&time,&schedule,&frame)||owner)return 8;
 NFRenderHandoff*q=nf_render_handoff_create(p->epoch);if(!q||!nf_render_handoff_push(q,&frame)||frame)return 9;frame=nf_render_handoff_pop(q);nf_render_handoff_epoch(q,p->epoch+1);nf_render_handoff_close(q);free(b);free(h);free(t);free(p);const NFStableSceneSubmission*owned=nf_render_submission_stable_view(frame);if(!owned||render_stable_scene_submission(owned,args))return 10;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,result);if(memcmp(reference,result,bytes)||glGetError()!=GL_NO_ERROR)return 11;
 NFStableSceneSubmission*mutable=(NFStableSceneSubmission*)owned;mutable->proof.display_generation++;if(render_stable_scene_submission(owned,args)!=44)return 12;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,result);if(memcmp(reference,result,bytes))return 13;mutable->proof.display_generation--;if(render_stable_scene_submission(owned,args))return 14;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,result);if(memcmp(reference,result,bytes)||glGetError()!=GL_NO_ERROR)return 15;
 if(argc==6){FILE*f=fopen(argv[5],"wb");if(!f)return 17;fprintf(f,"P6\n3840 2160\n255\n");for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++)if(fwrite((uint8_t*)result+((2159-y)*3840+x)*4,1,3,f)!=3)return 18;fclose(f);}
 printf("PASS stable queued source-free epoch-drain close lifetime serial=%u refresh=%u exact_RGBA_pixels=8294400 malformed_gpu_unchanged=1 repeat_exact=1\n",owned->proof.serial,owned->proof.display_refresh);nf_render_submission_destroy(frame);nf_render_handoff_destroy(q);preview_shutdown();free(reference);free(result);return 0;}
