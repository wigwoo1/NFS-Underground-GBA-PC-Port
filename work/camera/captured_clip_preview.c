/* Exact-capture diagnostic only; launcher verifies SHA256 and epoch. */
#include "scene_packet.h"
static void captured_select(const NFScenePacket*);
static void captured_clip(int);
#define NF_DIAGNOSTIC_PACKET_SELECT captured_select
#define NF_DIAGNOSTIC_SURFACE_CLIP captured_clip
#ifdef NF_NATIVE_ROAD_VIEWPORT
static int captured_road_bounds(unsigned,double*,double*,double*,double*);
#define NF_DIAGNOSTIC_ROAD_BOUNDS captured_road_bounds
#endif
#define NF_DIAGNOSTIC_DEPTH
#ifdef NF_ISOLATE_SURFACE
static int isolate_command(unsigned index);
#define NF_DIAGNOSTIC_COMMAND_FILTER isolate_command
#endif
#include "packet_preview.c"
#ifdef NF_ISOLATE_SURFACE
static int isolate_command(unsigned index){const char*s=getenv("NF_ONLY_SURFACE");const char*t=getenv("NF_SECOND_SURFACE");return (s&&index==(unsigned)strtoul(s,NULL,10))||(t&&index==(unsigned)strtoul(t,NULL,10));}
#endif
static uint16_t captured_bounds[128][4];static uint32_t captured_kinds[128];
static void captured_select(const NFScenePacket*p){
 double owned_alpha;const uint8_t*owned_bounds;
 if(nf_scene_packet_bounds(p,&owned_alpha,&owned_bounds)){
  uint32_t count;memcpy(&count,p->section[1].data+4,4);if(fabs(owned_alpha-packet_presented_time.alpha)>1e-9)exit(34);
  for(unsigned i=0;i<count;i++){memcpy(captured_bounds[i],owned_bounds+i*8,8);memcpy(captured_kinds+i,p->section[4].data+8+i*20,4);}return;
 }
 const char*path=getenv("NF_CAPTURE_CLIPS");FILE*f=path?fopen(path,"rb"):NULL;uint32_t h[5],count;
 memcpy(&count,p->section[1].data+4,4);
 if(!f||fread(h,4,5,f)!=5||h[0]!=0x3150434e||h[1]!=p->serial||h[2]!=p->begin_refresh||h[3]!=p->end_refresh||h[4]!=count||count>128)exit(31);
#ifdef NF_SAMPLED_CLIPS
 double expected;if(fread(&expected,sizeof(expected),1,f)!=1||!isfinite(expected)||expected<0||expected>=1||fabs(expected-packet_presented_time.alpha)>1e-9)exit(34);
#else
 if(packet_presented_time.alpha!=0)exit(31);
#endif
 for(unsigned i=0;i<count;i++){
  uint32_t id[5];if(fread(id,4,5,f)!=5||memcmp(id,p->section[4].data+8+i*20,20)||fread(captured_bounds[i],2,4,f)!=4)exit(32);captured_kinds[i]=id[0];
 }
 if(fgetc(f)!=EOF)exit(33);fclose(f);
#ifdef NF_NATIVE_ORDER
 /* Consume owned native command indices, never mutate the source packet. */
 static uint32_t selected_order[259];uint32_t oh[5],seen[257]={0};
 path=getenv("NF_NATIVE_ORDER_FILE");f=path?fopen(path,"rb"):NULL;
 unsigned commands=count+1;
 if(!f||fread(oh,4,5,f)!=5||oh[0]!=0x314f444e||oh[1]!=p->serial||oh[2]!=p->begin_refresh||oh[3]!=p->end_refresh||oh[4]!=commands||commands>257)exit(35);
 memcpy(selected_order,p->section[2].data,8);
 for(unsigned i=0;i<commands;i++){
  uint32_t index;if(fread(&index,4,1,f)!=1||index>=commands||seen[index]++)exit(36);
  memcpy(selected_order+2+i,p->section[2].data+8+index*4,4);
 }
 if(fgetc(f)!=EOF)exit(37);fclose(f);
 preview_memory[3]=(PreviewMemory){(const uint8_t*)selected_order,8+commands*4};
#endif
}
static void captured_clip(int ring){
 if(ring<0){glDisable(GL_SCISSOR_TEST);return;}
 /* Wall clipping only: road raster rules have not been established here. */
 if(captured_kinds[ring]!=2)return;
 const uint16_t*b=captured_bounds[ring];
 int l=b[0],r=b[1],t=b[2],bottom=b[3];
 if(l>240)l=240;if(r>240)r=240;if(t>160)t=160;if(bottom>160)bottom=160;
 int x0=(int)ceil(300+l*13.5-.5),x1=(int)ceil(300+r*13.5-.5);
 int y0=(int)ceil((160-bottom)*13.5-.5),y1=(int)ceil((160-t)*13.5-.5);
 glEnable(GL_SCISSOR_TEST);glScissor(x0,y0,x1>x0?x1-x0:0,y1>y0?y1-y0:0);
}


#ifdef NF_NATIVE_ROAD_VIEWPORT
static int captured_road_bounds(unsigned ring,double*left,double*right,double*top,double*bottom){
 if(ring>=128||captured_kinds[ring]!=1)return 0;
 /* Projected vertices and glOrtho use 240x160 source coordinates. */
 *left=captured_bounds[ring][0];*right=captured_bounds[ring][1];*top=captured_bounds[ring][2];*bottom=captured_bounds[ring][3];return 1;
}
#endif
