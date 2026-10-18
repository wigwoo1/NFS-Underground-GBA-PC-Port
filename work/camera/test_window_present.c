#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
#include "window_present.h"
#include "preview_warmup.h"
#include "preview_availability.h"
#include "presentation_hold.h"
int main(int argc,char**argv){
 if(argc!=3)return 1;
 NFSnapshotStore*s=nf_snapshot_create(32*1024*1024);NFScenePacket a,b;
 if(!s||!enqueue_file(s,argv[1],&a)||!enqueue_file(s,argv[2],&b))return 2;
 preview_window_output=1;preview_keep_context=1;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 char*args[]={argv[0],"unused","unused","unused"};int result=render_packet_at(s,(a.end_refresh+b.end_refresh)/2.0,args);if(result)return result;
 size_t source_size=3840*2160*3,target_size=1280*720*3;uint8_t*source=malloc(source_size),*target=malloc(target_size);if(!source||!target)return 3;
 glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,source);
 if(!preview_draw_warmup()||render_packet_at(s,(a.end_refresh+b.end_refresh)/2.0,args))return 9;
 uint8_t*after_warm=malloc(source_size);if(!after_warm)return 10;
 glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,after_warm);
 int warm_equal=memcmp(source,after_warm,source_size)==0;free(after_warm);if(!warm_equal)return 11;
 printf("warmup_framebuffer_byte_identical=1 compared_4k_bytes=%llu\n",(unsigned long long)source_size);

 void(APIENTRY*bind)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");
 void(APIENTRY*gen)(GLsizei,GLuint*)=(void*)wglGetProcAddress("glGenFramebuffers");
 void(APIENTRY*attach)(GLenum,GLenum,GLenum,GLuint,GLint)=(void*)wglGetProcAddress("glFramebufferTexture2D");
 GLuint fbo,texture;glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);glTexImage2D(GL_TEXTURE_2D,0,GL_RGB,1280,720,0,GL_RGB,GL_UNSIGNED_BYTE,NULL);
 gen(1,&fbo);bind(0x8d40,fbo);attach(0x8d40,0x8ce0,GL_TEXTURE_2D,texture,0);
 if(!preview_window_stage_to(1,fbo,1280,720))return 4;
 bind(0x8ca8,fbo);glReadBuffer(0x8ce0);glReadPixels(0,0,1280,720,GL_RGB,GL_UNSIGNED_BYTE,target);
 unsigned mismatch=0;for(unsigned y=0;y<720;y++)for(unsigned x=0;x<1280;x++)for(unsigned c=0;c<3;c++)mismatch+=target[(y*1280+x)*3+c]!=source[((y*3+1)*3840+x*3+1)*3+c];
 NFPresentationHold hold={0};nf_presentation_hold(&hold,1,100,1,NF_TIME_READY);
 for(unsigned step=1;step<=2;step++){
  int repeated=nf_presentation_hold(&hold,1,100+step,0,NF_TIME_AFTER);
  if(!repeated||!preview_window_stage_to(repeated,fbo,1280,720))return 24;
  bind(0x8ca8,fbo);glReadPixels(0,0,1280,720,GL_RGB,GL_UNSIGNED_BYTE,target);
  for(unsigned y=0;y<720;y++)for(unsigned x=0;x<1280;x++)for(unsigned c=0;c<3;c++)
   if(target[(y*1280+x)*3+c]!=source[((y*3+1)*3840+x*3+1)*3+c])return 25;
 }
 int expired=nf_presentation_hold(&hold,1,103,0,NF_TIME_AFTER);
 if(expired||!preview_window_stage_to(expired,fbo,1280,720))return 26;
 bind(0x8ca8,fbo);glReadPixels(0,0,1280,720,GL_RGB,GL_UNSIGNED_BYTE,target);
 for(size_t i=0;i<target_size;i++)if(target[i])return 27;
 printf("held_framebuffer_exact_for_two_refreshes=1 expired_hold_clears=1\n");
 /* Inject a structurally valid new model identity across a scene boundary. */
 NFSnapshotPair pair;NFScenePacket va,vb;void*copy_a=NULL,*copy_b=NULL;size_t size_a=0,size_b=0;
 double midpoint=(a.end_refresh+b.end_refresh)/2.0;
 if(nf_snapshot_acquire(s,midpoint,0,&pair)!=NF_TIME_READY||
    !nf_scene_packet_view(pair.older,pair.older_size,&va)||!nf_scene_packet_view(pair.newer,pair.newer_size,&vb)||
    !nf_scene_packet_build(&va,&copy_a,&size_a)||!nf_scene_packet_build(&vb,&copy_b,&size_b))return 12;
 nf_snapshot_release(s);
 if(!nf_scene_packet_view(copy_b,size_b,&vb))return 13;
 uint8_t*identity=(uint8_t*)vb.section[4].data+vb.section[4].size-20+4;identity[0]^=4;
 if(!nf_scene_packet_push(s,2,copy_a,size_a)||!nf_scene_packet_push(s,2,copy_b,size_b))return 14;
 int ready=1,incompatible=0;
 if(preview_render_available(s,midpoint,args,&ready,&incompatible)||ready||!incompatible)return 15;
 if(!preview_window_stage_to(ready,fbo,1280,720))return 6;
 bind(0x8ca8,fbo);glReadBuffer(0x8ce0);glReadPixels(0,0,1280,720,GL_RGB,GL_UNSIGNED_BYTE,target);
 unsigned nonblack=0;for(size_t i=0;i<target_size;i++)nonblack+=target[i]!=0;
 /* Rejection must release its snapshot pins so the next epoch can arrive. */
 identity[0]^=4;
 if(!nf_scene_packet_push(s,3,copy_a,size_a)||!nf_scene_packet_push(s,3,copy_b,size_b))return 16;
 ready=1;
 bind(0x8d40,preview_fbo);
 if(preview_render_available(s,midpoint,args,&ready,&incompatible)||!ready||incompatible)return 17;
 uint8_t*recovered=malloc(source_size);if(!recovered)return 18;
 glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,recovered);
 int recovered_equal=!memcmp(source,recovered,source_size);free(recovered);
 if(!recovered_equal)return 19;
 ready=1;
 if(preview_render_available(s,-1,args,&ready,&incompatible)!=23)return 20;
 printf("incompatible_pair_cleared=1 snapshot_unpinned=1 recovery_byte_identical=1 invalid_target_still_fatal=1\n");
 RoadPreview thin={0};NFPoint3 endpoints[2]={{0,0,1000},{1,0,1000}};double projection[3]={120,80,120};int shades[3240];
 unsigned narrow_before=lighting_native_narrow,range_before=lighting_range_fallback;
 if(wall_shades(&thin,endpoints,projection,shades)!=2||lighting_native_narrow!=narrow_before+1)return 21;
 endpoints[1].x=10;
 if(wall_shades(&thin,endpoints,projection,shades)!=2||lighting_native_narrow!=narrow_before+2)return 22;
 endpoints[0].z=endpoints[1].z=40000;
 if(wall_shades(&thin,endpoints,projection,shades)||lighting_range_fallback!=range_before+1)return 23;
 printf("lighting_zero_and_one_column_classification=1 lighting_range_classification=1\n");
 nf_scene_packet_free(copy_a);nf_scene_packet_free(copy_b);
 if(!preview_window_stage(1)||!preview_window_finish()||!preview_window_stage(0)||!preview_window_finish())return 7;
 void(APIENTRY*remove)(GLsizei,const GLuint*)=(void*)wglGetProcAddress("glDeleteFramebuffers");remove(1,&fbo);glDeleteTextures(1,&texture);
 printf("mismatched_channels=%u nonblack_loading_channels=%u compared_channels=%llu contexts=%u\n",mismatch,nonblack,(unsigned long long)target_size,preview_contexts);
 free(source);free(target);preview_shutdown();nf_snapshot_destroy(s);return mismatch||nonblack?8:0;
}
