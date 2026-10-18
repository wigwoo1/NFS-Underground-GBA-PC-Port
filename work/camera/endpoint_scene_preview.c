#define NF_PACKET_NO_MAIN
#include "scene_packet.h"
static void endpoint_select(const NFScenePacket*);
static void endpoint_clip(int);
static void endpoint_model_clip(int);
static int endpoint_road(unsigned,double*,double*,double*,double*);
#define NF_DIAGNOSTIC_PACKET_SELECT endpoint_select
#define NF_DIAGNOSTIC_SURFACE_CLIP endpoint_clip
#define NF_DIAGNOSTIC_MODEL_CLIP endpoint_model_clip
#define NF_DIAGNOSTIC_ROAD_BOUNDS endpoint_road
#ifndef NF_ENDPOINT_NO_DEPTH
#define NF_DIAGNOSTIC_DEPTH
#define NF_SOURCE_COMMAND_ORDER
#endif
static int endpoint_command(unsigned);
#define NF_DIAGNOSTIC_COMMAND_FILTER endpoint_command
#include "packet_preview.c"
#include "endpoint_surface_bounds.h"
static int endpoint_command(unsigned command){
 const char*list=getenv("NF_ENDPOINT_COMMANDS");
 if(list){while(*list){char*end;unsigned long value=strtoul(list,&end,10);if(end==list)return 0;if(command==(unsigned)value)return 1;if(*end!=',')return 0;list=end+1;}return 0;}
 const char*value=getenv("NF_ENDPOINT_COMMAND");if(!value)return 1;if(!strcmp(value,"world"))return command<UINT32_MAX-15;if(!strcmp(value,"model"))return command>=UINT32_MAX-15;return command==(unsigned)strtoul(value,NULL,10);
}
int main(int argc,char**argv){
 if(argc!=3)return 1;FILE*f=fopen(argv[1],"rb");if(!f)return 2;
 fseek(f,0,SEEK_END);long bytes=ftell(f);rewind(f);if(bytes<96||bytes>64*1024*1024)return 3;
 void*data=malloc(bytes);NFScenePacket packet;if(!data||fread(data,1,bytes,f)!=(size_t)bytes||!nf_scene_packet_view(data,bytes,&packet))return 4;fclose(f);
 preview_zero_valid=1;preview_zero_background=1;preview_keep_context=1;
 const char*palette_path=getenv("NF_ENDPOINT_DISPLAY_PALETTE");
 if(palette_path){FILE*palette=fopen(palette_path,"rb");if(!palette){free(data);return 38;}int ok=fread(preview_display_palette,1,sizeof(preview_display_palette),palette)==sizeof(preview_display_palette)&&fgetc(palette)==EOF;fclose(palette);if(!ok){free(data);return 38;}preview_display_palette_valid=1;for(unsigned y=0;y<160;y++)preview_zero_colors[y]=preview_display_palette[y][0];}
 _putenv("NF_PREVIEW_PHASE=0");char*args[]={argv[0],argv[1],argv[1],argv[2]};NFTimelineSample time={0};time.alpha=0;
 const char*camera_path=getenv("NF_ENDPOINT_CAMERA_PAIR");
 if(camera_path){
  NFRigidPose cameras[2],check;FILE*camera=fopen(camera_path,"rb");if(!camera){free(data);return 35;}
  int ok=fread(cameras,1,sizeof(cameras),camera)==sizeof(cameras)&&fgetc(camera)==EOF;if(fclose(camera))ok=0;
  const uint8_t*bounds;if(!ok||!nf_scene_packet_bounds(&packet,&time.alpha,&bounds)||!nf_pose_sample(cameras,cameras,0,&check)||!nf_pose_sample(cameras+1,cameras+1,0,&check)){free(data);return 35;}
  memcpy(packet_source_cameras,cameras,sizeof(cameras));packet_continuous_camera=1;
 }
 NFRigidPose*command_cameras=NULL;const char*command_camera_path=getenv("NF_ENDPOINT_COMMAND_CAMERAS");
 if(command_camera_path){FILE*camera=fopen(command_camera_path,"rb");if(!camera){free(data);return 37;}int ok=!fseek(camera,0,SEEK_END);long length=ok?ftell(camera):-1;rewind(camera);
  ok=ok&&length>0&&length<=144*(long)sizeof(NFRigidPose)&&length%(long)sizeof(NFRigidPose)==0;
  if(ok){command_cameras=malloc((size_t)length);ok=command_cameras&&fread(command_cameras,1,(size_t)length,camera)==(size_t)length&&fgetc(camera)==EOF;}
  if(fclose(camera))ok=0;if(ok){preview_command_camera_count=(unsigned)(length/sizeof(NFRigidPose));NFRigidPose checked;for(unsigned i=0;ok&&i<preview_command_camera_count;i++)ok=nf_pose_sample(command_cameras+i,command_cameras+i,0,&checked);}
  if(!ok){free(command_cameras);free(data);return 37;}preview_command_cameras=command_cameras;
 }
 int result=render_packet_views(packet,packet,time,args);
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 const char*edge_path=getenv("NF_ENDPOINT_ROAD_EDGE_TRACE");
 if(edge_path&&!result){FILE*edge=fopen(edge_path,"wb");if(!edge)result=36;else{
  int ok=fprintf(edge,"ring,edge,crossing,z0,z1,u,v,x0,y0,x1,y1,shift,height,affine,a0,a1,a2,a3,offset0,offset1\n")>0;
  for(unsigned i=0;i<road_clip_edge_count;i++){const NFRoadClipEdgeTrace*r=road_clip_edges+i;
   if(fprintf(edge,"%u,%u,%u,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%u,%u,%u,%d,%d,%d,%d,%d,%d\n",r->ring,r->edge,r->crossing,r->z0,r->z1,r->u,r->v,r->camera0.x,r->camera0.y,r->camera1.x,r->camera1.y,r->shift,r->height,r->affine,r->attrs[0],r->attrs[1],r->attrs[2],r->attrs[3],r->offsets[0],r->offsets[1])<0)ok=0;
  }if(fclose(edge))ok=0;if(!ok)result=36;
 }}
#endif
 preview_shutdown();preview_command_cameras=NULL;preview_command_camera_count=0;free(command_cameras);free(data);return result;
}
