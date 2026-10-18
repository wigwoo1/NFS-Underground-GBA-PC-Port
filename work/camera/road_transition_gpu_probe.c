#define NF_PACKET_NO_MAIN
#define NF_PACKET_NO_FILES
#define NF_DIAGNOSTIC_DEPTH
static int transition_uv_mode;
#define NF_DIAGNOSTIC_ROAD_UV_POLICY transition_uv_mode
static int transition_bounds(unsigned,double*,double*,double*,double*);
static void transition_surface_clip(int);
static int transition_hud(void);
#define NF_DIAGNOSTIC_HUD_DRAW transition_hud
#define NF_DIAGNOSTIC_SURFACE_CLIP transition_surface_clip
#define NF_DIAGNOSTIC_ROAD_BOUNDS transition_bounds
#include "packet_preview.c"
#include "layer_snapshot.h"
static int hud_preview;static uint64_t hud_epoch;static unsigned hud_refresh,hud_drawn,hud_failed;
static const NFHudLayerRow*transition_hud_rows;
static int transition_layer_read(uint64_t epoch,unsigned refresh,unsigned row,void*out,unsigned size){if(!transition_hud_rows||!out||epoch!=hud_epoch||refresh!=hud_refresh||row>=160||size!=sizeof(NFHudLayerRow))return 0;memcpy(out,transition_hud_rows+row,size);return 1;}
static int(*layer_read)(uint64_t,unsigned,unsigned,void*,unsigned)=transition_layer_read;
#include "live_hud_gpu.h"
static int transition_hud(void){return endpoint_hud();}
__declspec(dllexport) int nf_scene_transition_gpu_hud(const void*data,size_t size){
 if(!data||size!=32+160*sizeof(NFHudLayerRow))return 0;uint32_t h[4];uint64_t epoch;memcpy(h,data,16);memcpy(&epoch,(const uint8_t*)data+16,8);
 if(h[0]!=0x3148464e||h[1]!=sizeof(NFHudLayerRow)||h[2]!=160||!epoch)return 0;
 const NFHudLayerRow*rows=(const NFHudLayerRow*)((const uint8_t*)data+32);for(unsigned y=0;y<160;y++)if(rows[y].refresh!=h[3]||rows[y].row!=y)return 0;
 transition_hud_rows=rows;hud_epoch=epoch;hud_refresh=h[3];hud_preview=1;preview_zero_background=1;for(unsigned y=0;y<160;y++)memcpy(preview_zero_colors+y,rows[y].palette,2);return 1;
}
static uint16_t transition_rects[128][4];static int transition_use_bounds;
static NFScenePacket transition_packet;static uint32_t transition_kinds[128];
static void transition_surface_clip(int ring){if(ring<0){glDisable(GL_SCISSOR_TEST);return;}if(!transition_use_bounds||transition_kinds[ring]!=2)return;const uint16_t*b=transition_rects[ring];int x0=(int)ceil(300+b[0]*13.5-.5),x1=(int)ceil(300+b[1]*13.5-.5),y0=(int)ceil((160-b[3])*13.5-.5),y1=(int)ceil((160-b[2])*13.5-.5);glEnable(GL_SCISSOR_TEST);glScissor(x0,y0,x1>x0?x1-x0:0,y1>y0?y1-y0:0);}
static double transition_projection[3];
static NFRigidPose transition_native_camera;
static double transition_capture_alpha;
__declspec(dllexport) int nf_road_transition_gpu_capture_alpha(double*out){if(!out||!road_count)return 0;*out=transition_capture_alpha;return 1;}
__declspec(dllexport) int nf_road_transition_gpu_native_camera(NFRigidPose out[2]){if(!out||!road_count)return 0;out[0]=out[1]=transition_native_camera;return 1;}
static int transition_selected_ring=-1;
__declspec(dllexport) int nf_road_transition_gpu_bounds(unsigned ring,uint16_t out[4]){if(!out||ring>=road_count||!preview_road_attributes_present[ring])return 0;memcpy(out,transition_rects[ring],8);return 1;}
__declspec(dllexport) int nf_road_transition_gpu_uv_mode(int mode){if(mode<0||mode>2)return 0;transition_uv_mode=mode;return 1;}
__declspec(dllexport) int nf_road_transition_gpu_select(int ring){if(ring<-1||ring>=(int)road_count||(ring>=0&&!preview_road_attributes_present[ring]))return 0;transition_selected_ring=ring;return 1;}
static int transition_bounds(unsigned ring,double*l,double*r,double*t,double*b){
 if(!transition_use_bounds||ring>=road_count||!preview_road_attributes_present[ring])return 0;
 *l=transition_rects[ring][0];*r=transition_rects[ring][1];*t=transition_rects[ring][2];*b=transition_rects[ring][3];return 1;
}
__declspec(dllexport) int nf_road_transition_gpu_init(const void*data,size_t size,const char*reciprocal_path){
 NFScenePacket packet;NFSceneSection model;if(!nf_scene_packet_view(data,size,&packet)||!nf_scene_packet_model(&packet,0,&model))return 1;
 memcpy(transition_projection,model.data+24,24);memcpy(&transition_native_camera,model.data+48,sizeof(transition_native_camera));double alpha;const uint8_t*bounds;
 if(!nf_scene_packet_bounds(&packet,&alpha,&bounds))return 2;
 transition_capture_alpha=alpha;
 transition_packet=packet;
 NFWorldMetadata metadata[128];unsigned count;if(!nf_scene_world_metadata_all(packet.section[1],metadata,128,&count))return 3;
 int context=preview_context_open();if(context)return 40+context;if(!preview_road_table_load_path(reciprocal_path))return 4;preview_generation++;preview_keep_context=1;preview_zero_valid=1;
 for(unsigned i=0;i<count;i++){memcpy(transition_rects[i],bounds+i*8,8);memcpy(transition_kinds+i,packet.section[4].data+8+i*20,4);}
 for(unsigned i=0;i<count;i++)if(metadata[i].mode==5||metadata[i].mode==6){
  if(!nf_scene_world_road_attributes(packet.section[1],i,preview_road_attributes+i))return 5;
  preview_road_attributes_present[i]=1;preview_world_indices[i]=metadata[i].data;preview_world_affine[i]=metadata[i].mode==6;memcpy(transition_rects[i],bounds+i*8,8);
 }
 preview_memory[2]=(PreviewMemory){packet.section[1].data,packet.section[1].size};int loaded=load_roads("retained-transition-world");memset(preview_memory,0,sizeof(preview_memory));return loaded?0:6;
}
__declspec(dllexport) int nf_road_transition_gpu_render(const NFRigidPose*camera,double alpha,int use_bounds,uint8_t*rgb,float*depth){
 if(!camera||!rgb||!depth||!isfinite(alpha)||alpha<0||alpha>1)return 1;transition_use_bounds=use_bounds;
 glViewport(300,0,3240,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,240,160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glDisable(GL_SCISSOR_TEST);glEnable(GL_TEXTURE_2D);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5f);glClearColor(0,0,0,1);glPixelStorei(GL_PACK_ALIGNMENT,1);
 glEnable(GL_DEPTH_TEST);glDepthFunc(GL_GEQUAL);glDepthMask(GL_TRUE);glClearDepth(0);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
 NFRigidPose poses[2]={camera[0],camera[1]};
 for(unsigned ring=0;ring<road_count;ring++)if(preview_road_attributes_present[ring]&&(transition_selected_ring<0||ring==(unsigned)transition_selected_ring)&&!draw_road_range(poses,alpha,transition_projection,ring,ring+1))return 2;
 glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,rgb);glReadPixels(0,0,3840,2160,GL_DEPTH_COMPONENT,GL_FLOAT,depth);return glGetError()==GL_NO_ERROR?0:3;
}
__declspec(dllexport) void nf_road_transition_gpu_close(void){preview_shutdown();hud_background=hud_program=obj_affine_program=0;hud_preview=preview_zero_background=0;transition_hud_rows=NULL;}
__declspec(dllexport) int nf_scene_transition_gpu_counters(uint64_t out[4]){if(!out)return 0;out[0]=world_zero_draws;out[1]=wall_zero_draws;out[2]=model_zero_draws;out[3]=lighting_fallback;return 1;}
/* Full retained geometry consumer: original order, wall classifications and
   lighting, all models, same source camera. Hardware HUD is not in this packet. */
__declspec(dllexport) int nf_scene_transition_gpu_render(const NFRigidPose*camera,double alpha,int use_bounds,uint8_t*rgb,float*depth){
 if(!camera||!rgb||!depth||!isfinite(alpha)||alpha<0||alpha>1)return 1;
 NFScenePacket*p=&transition_packet;NFWorldMetadata metadata[128];unsigned count;
 if(!nf_scene_world_metadata_all(p->section[1],metadata,128,&count))return 2;
 transition_use_bounds=use_bounds;packet_continuous_camera=1;memcpy(packet_source_cameras,camera,sizeof(packet_source_cameras));
 for(unsigned i=0;i<count;i++){
  unsigned mode=metadata[i].mode;
  if(mode==5||mode==6){memcpy(preview_road_attributes+i,metadata[i].data+metadata[i].size-sizeof(NFRoadSourceAttributes),sizeof(NFRoadSourceAttributes));preview_road_attributes_present[i]=1;preview_world_indices[i]=metadata[i].data;preview_world_affine[i]=mode==6;}
  else if(mode==2||mode==3){preview_wall_states[i]=metadata[i].data;preview_wall_planes[i]=mode==3?17:1;}
  else if(mode)return 3;
 }
 size_t bytes;uint8_t*model=packet_pair_model(p,p,0,&bytes);if(!model){packet_extra_release();return 4;}
 unsigned models=nf_scene_packet_model_count(p);
 for(unsigned i=1;i<models;i++){size_t n;uint8_t*extra=packet_pair_model(p,p,i,&n);if(!extra){free(model);packet_extra_release();return 4;}preview_extra_models[preview_extra_count++]=(PreviewMemory){extra,n};}
 preview_memory[0]=(PreviewMemory){model,bytes};uint32_t empty[2]={0x31574650,0};preview_memory[1]=(PreviewMemory){(const uint8_t*)empty,8};
 for(unsigned i=1;i<=3;i++)preview_memory[i+1]=(PreviewMemory){p->section[i].data,p->section[i].size};
 preview_alpha_override=alpha;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 char*args[]={"retained-scene","packet-model","unused","packet-wireframe","packet-world","packet-order","packet-lighting"};
 int result=legacy_preview_main(7,args);memset(preview_memory,0,sizeof(preview_memory));packet_extra_release();free(model);if(result)return 100+result;
 glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,rgb);glReadPixels(0,0,3840,2160,GL_DEPTH_COMPONENT,GL_FLOAT,depth);return glGetError()==GL_NO_ERROR?0:5;
}
