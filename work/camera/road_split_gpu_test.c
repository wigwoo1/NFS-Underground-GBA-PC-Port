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
static void*load(const char*path,size_t*size){FILE*f=fopen(path,"rb");if(!f)return NULL;fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);if(n<=0||n>64*1024*1024){fclose(f);return NULL;}void*p=malloc(n);if(!p||fread(p,1,n,f)!=(size_t)n){free(p);fclose(f);return NULL;}fclose(f);*size=n;return p;}
int main(int argc,char**argv){if(argc!=5&&argc!=6&&argc!=7)return 1;size_t as,bs,ps;void*a=load(argv[1],&as),*b=load(argv[2],&bs),*palette=load(argv[3],&ps);unsigned cut=atoi(argv[4]);if(!a||!b||!palette||ps!=81920)return 2;
 memcpy(preview_display_palette,palette,ps);preview_zero_valid=preview_display_palette_valid=preview_measure_only=preview_keep_context=1;_putenv("NF_PREVIEW_PHASE=0");char*args[]={argv[0],"unused","unused","unused"};size_t bytes=3840u*2160u*4;uint8_t*old=malloc(bytes),*newer=malloc(bytes),*mixed=malloc(bytes),*repeat=malloc(bytes);if(!old||!newer||!mixed||!repeat)return 3;
 int rc=render_road_bundle(a,as,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,old);rc=render_road_bundle(b,bs,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,newer);
 rc=render_road_split(a,as,b,bs,cut,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,mixed);unsigned edge=(unsigned)ceil(cut*13.5-.5),changed=0;
 for(unsigned y=0;y<2160;y++){size_t at=(size_t)y*3840*4;uint8_t*expected=(2159-y<edge?old:newer)+at;if(memcmp(mixed+at,expected,3840*4)){printf("row_mismatch=%u\n",y);return 4;}for(unsigned x=0;x<3840;x++)if(memcmp(old+at+x*4,newer+at+x*4,3))changed++;}
 rc=render_road_split(a,as,b,bs,cut,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,repeat);if(memcmp(mixed,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 5;
 if(render_road_split(a,as,b,bs,0,args)!=44||render_road_split(a,as,b,bs,160,args)!=44||render_road_split(b,bs,a,as,cut,args)!=44)return 6;
 if(getenv("NF_TEST_SPLIT_CONTEXT_REOPEN")){preview_shutdown();if(preview_split_scratch)return 26;rc=render_road_split(a,as,b,bs,cut,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,repeat);if(memcmp(mixed,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 27;printf("split_context_reopen_rgba_exact=1\n");}
 if(argc>=6){size_t ts=0;uint8_t*text=NULL,*text_indices=NULL,*text_coverage=NULL;if(argc==7){text=load(argv[6],&ts);if(!text||ts!=76832||nf_bundle_word(text)!=0x5854464e||nf_bundle_word(text+4)!=1||nf_bundle_word(text+20)!=240||nf_bundle_word(text+24)!=160||nf_bundle_word(text+28)!=38400)return 14;text_indices=text+32;text_coverage=text+38432;for(unsigned i=0;i<38400;i++)if(text_coverage[i]>1)return 14;}
 size_t hs;void*hud=load(argv[5],&hs);if(!hud||(text&&nf_bundle_word(text+16)!=nf_bundle_word(hud))||!owned_hud_gpu_draw(hud,hs,text_indices,text_coverage))return 7;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,repeat);unsigned hud_changed=0;for(size_t i=0;i<bytes;i+=4)if(memcmp(mixed+i,repeat+i,3))hud_changed++;if(!hud_changed)return 8;
 rc=render_road_split(a,as,b,bs,cut,args);if(rc||!owned_hud_gpu_draw(hud,hs,text_indices,text_coverage))return 9;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,old);if(memcmp(old,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 10;
 if(!nf_live_rgb_reference(repeat,3840u*2160u))return 25;
 unsigned reference_pixels=0;uint8_t vram[0x18000]={0};uint32_t colors[240],tags[240];uint8_t controls[240],backdrop_controls[240];
 for(unsigned row_index=0;row_index<160;row_index++){NFHudLayerRow row;memcpy(&row,(uint8_t*)hud+row_index*sizeof(row),sizeof(row));memcpy(vram+0x10000,row.obj_vram,0x8000);uint16_t window[6];for(unsigned i=0;i<6;i++)window[i]=owned_hud_half(row.registers+64+i*2);unsigned display=owned_hud_half(row.registers),blend=owned_hud_half(row.registers+80),alpha=owned_hud_half(row.registers+82),brightness=owned_hud_half(row.registers+84),priority=owned_hud_half(row.registers+12)&3;
 if(!nf_obj_window_scanline_prepared(vram,sizeof(vram),row.palette,1024,row.oam,1024,display,row_index,window,blend,brightness,colors,tags,controls,backdrop_controls))return 11;
 unsigned bd=owned_hud_half(row.palette);uint32_t backdrop=0xff000000u|(((bd&31)<<3)|((bd&31)>>2))|(((((bd>>5)&31)<<3)|(((bd>>5)&31)>>2))<<8)|(((((bd>>10)&31)<<3)|(((bd>>10)&31)>>2))<<16);
 for(unsigned yy=(unsigned)ceil(row_index*13.5-.5);yy<(unsigned)ceil((row_index+1)*13.5-.5);yy++)for(unsigned xx=300;xx<3540;xx++){unsigned cell=(unsigned)floor((xx+.5-300)/13.5);size_t at=((size_t)(2159-yy)*3840+xx)*4;uint8_t*bg_pixel=mixed+at;unsigned control=controls[cell];if(!(display&0x400))control&=~4u;uint32_t bg=(control&4)&&bg_pixel[3]>=128?0xff000000u|bg_pixel[0]|((uint32_t)bg_pixel[1]<<8)|((uint32_t)bg_pixel[2]<<16):0;
 if(text_coverage&&text_coverage[row_index*240+cell]){unsigned c=owned_hud_half(row.palette+text_indices[row_index*240+cell]*2);uint32_t tc=0xff000000u|(((c&31)<<3)|((c&31)>>2))|(((((c>>5)&31)<<3)|(((c>>5)&31)>>2))<<8)|(((((c>>10)&31)<<3)|(((c>>10)&31)>>2))<<16);bg=(control&4)?tc:0;}
 uint32_t object=(control&16)?colors[cell]:0;unsigned b=(control&32)?blend:blend&0x3f00;
 if(!bg&&!object&&((control^backdrop_controls[cell])&32)&&((blend>>6)&3)>=2&&(blend&32))return 12;
 uint32_t expected=nf_obj_bg_backdrop_pixel(object,tags[cell]|0x20000,bg,priority,backdrop,b,alpha,brightness);if(memcmp(repeat+at,&expected,4)){printf("hud_cpu_mismatch=%u,%u expected=%08x actual=%02x%02x%02x%02x\n",xx,yy,expected,repeat[at+3],repeat[at+2],repeat[at+1],repeat[at]);return 13;}reference_pixels++;
 }}printf("hud_cpu_reference_pixels=%u\n",reference_pixels);
 if(text){NFRoadBundle av,bv;NFHudSubmissionView view,sentinel;memset(&sentinel,0xa5,sizeof(sentinel));view=sentinel;if(!nf_road_bundle_view(a,as,&av)||!nf_road_bundle_view(b,bs,&bv)||!nf_hud_submission_view(&av,&bv,hud,hs,text,ts,cut,&view))return 15;
 unsigned rejected=0;uint32_t*header=(uint32_t*)text;
 for(unsigned word=0;word<8;word++){uint32_t saved=header[word];header[word]^=1;view=sentinel;if(nf_hud_submission_view(&av,&bv,hud,hs,text,ts,cut,&view)||memcmp(&view,&sentinel,sizeof(view)))return 16;header[word]=saved;rejected++;}
 uint8_t saved=text_coverage[0];text_coverage[0]=2;view=sentinel;if(nf_hud_submission_view(&av,&bv,hud,hs,text,ts,cut,&view)||memcmp(&view,&sentinel,sizeof(view)))return 17;text_coverage[0]=saved;rejected++;
 if(render_road_split_hud(a,as,b,bs,hud,hs,text,ts,cut+1,args)!=44)return 18;rejected++;
 glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,old);if(memcmp(old,repeat,bytes))return 19;
 rc=render_road_split_hud(a,as,b,bs,hud,hs,text,ts,cut,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,old);if(memcmp(old,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 20;
 NFOrderedSceneSubmission*owner=(NFOrderedSceneSubmission*)(uintptr_t)123;
 if(nf_ordered_scene_submission_create(a,as,b,bs,hud,hs,text,ts,cut+1,&owner)||owner!=(NFOrderedSceneSubmission*)(uintptr_t)123)return 21;
 if(!nf_ordered_scene_submission_create(a,as,b,bs,hud,hs,text,ts,cut,&owner))return 22;
 free(a);a=NULL;free(b);b=NULL;free(hud);hud=NULL;free(text);text=NULL;
 NFTimelineSample time={owner->epoch,av.ordered.packet.serial,bv.ordered.packet.serial,1,owner->refresh+0.5};NFSubmissionSchedule schedule={0};NFRenderSubmission*frame=NULL;NFRenderHandoff*queue=nf_render_handoff_create(owner->epoch);if(!queue||!nf_render_submission_ordered(&owner,&time,&schedule,&frame)||owner||!nf_render_handoff_push(queue,&frame)||frame)return 24;frame=nf_render_handoff_pop(queue);nf_render_handoff_close(queue);const NFOrderedSceneSubmission*queued=nf_render_submission_ordered_view(frame);rc=render_ordered_scene_submission(queued,args);if(rc)return rc;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,old);if(memcmp(old,repeat,bytes)||glGetError()!=GL_NO_ERROR)return 23;
 printf("owned_submission_source_free_render_exact=1 epoch=%llu refresh=%u\n",(unsigned long long)queued->epoch,queued->refresh);nf_render_submission_destroy(frame);nf_render_handoff_destroy(queue);printf("queued_ordered_source_free_closed_render_exact=1\n");
 printf("integrated_owned_submission_rgba_exact=1 malformed_preflight_rejections=%u\n",rejected);}
 printf("owned_hud_obj_changed_pixels=%u hud_repeat_rgba_exact=1 candidate_rows=%u text_included=%u\n",hud_changed,hud_candidate_builds,argc==7);free(text);free(hud);}
 printf("PASS split_row=%u cut4k=%u exact_pixels=8294400 page_difference_pixels=%u repeat_rgba_exact=1 alpha_preserved=1 invalid_cuts_order_rejected=1\n",cut,edge,changed);preview_shutdown();free(a);free(b);free(palette);free(old);free(newer);free(mixed);free(repeat);return 0;}


