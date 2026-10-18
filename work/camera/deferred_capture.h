typedef struct {uint64_t epoch,older,newer,capture_ns,rings,crossings;double alpha,target;unsigned older_refresh,newer_refresh,hud_refresh;} NFDeferredCaptureSource;
static NFDeferredCaptureSource deferred_capture_sources[12];static unsigned deferred_capture_source_count;
static unsigned deferred_capture_start=180;
static unsigned deferred_capture_uv_trigger;
static unsigned deferred_capture_model_trigger;
static NFRigidPose deferred_camera_poses[12][3];
#ifdef NF_NATIVE_ENDPOINT_RENDER
static NFHudLayerRow*deferred_hud_rows[12];static int deferred_hud_failed;
static void deferred_capture_hud(unsigned index,uint64_t epoch,unsigned refresh){
 if(index>=12||deferred_hud_rows[index]||!layer_read){deferred_hud_failed=1;return;}
 NFHudLayerRow*rows=malloc(160*sizeof(*rows));if(!rows){deferred_hud_failed=1;return;}
 for(unsigned y=0;y<160;y++)if(!layer_read(epoch,refresh,y,rows+y,sizeof(*rows))||rows[y].refresh!=refresh||rows[y].row!=y){free(rows);deferred_hud_failed=1;return;}
 deferred_hud_rows[index]=rows;
}
#endif
static uint8_t*deferred_native_packet;static size_t deferred_native_packet_size;static int deferred_native_packet_failed;
static uint8_t*deferred_native_packets[12];static size_t deferred_native_packet_sizes[12],deferred_native_packets_bytes;
static void deferred_capture_native_packets(const void*packet,unsigned index){
 if(index>=12||deferred_native_packets[index]){deferred_native_packet_failed=1;return;}
 uint32_t size;memcpy(&size,(const uint8_t*)packet+8,4);
 if(size<96||size>64u*1024u*1024u-deferred_native_packets_bytes){deferred_native_packet_failed=1;return;}
 uint8_t*copy=malloc(size);if(!copy){deferred_native_packet_failed=1;return;}memcpy(copy,packet,size);deferred_native_packets[index]=copy;deferred_native_packet_sizes[index]=size;deferred_native_packets_bytes+=size;
}
static void deferred_capture_native_packet(const void*packet){
 uint32_t size;memcpy(&size,(const uint8_t*)packet+8,4);if(size<96||size>64*1024*1024){deferred_native_packet_failed=1;return;}
 deferred_native_packet=malloc(size);if(!deferred_native_packet){deferred_native_packet_failed=1;return;}memcpy(deferred_native_packet,packet,size);deferred_native_packet_size=size;
}
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
static NFRoadClipEdgeTrace deferred_road_edges[49152];static unsigned deferred_road_indices[49152],deferred_road_edge_count;
static void deferred_capture_road_edges(unsigned index){
 for(unsigned i=0;i<road_clip_edge_count&&deferred_road_edge_count<49152;i++){deferred_road_indices[deferred_road_edge_count]=index;deferred_road_edges[deferred_road_edge_count++]=road_clip_edges[i];}
}
#endif
static void deferred_capture_source(unsigned index,uint64_t now,const NFTimelineSample*t,unsigned older_refresh,unsigned newer_refresh,unsigned hud_refresh,uint64_t rings,uint64_t crossings){
 if(index>=12)return;deferred_capture_sources[index]=(NFDeferredCaptureSource){t->epoch,t->older,t->newer,now,rings,crossings,t->alpha,t->target,older_refresh,newer_refresh,hud_refresh};if(index>=deferred_capture_source_count)deferred_capture_source_count=index+1;
 if(getenv("NF_CAPTURE_CAMERA_PAIRS")){memcpy(deferred_camera_poses[index],packet_source_cameras,sizeof(packet_source_cameras));deferred_camera_poses[index][2]=packet_presented_camera;}
#ifdef NF_NATIVE_ENDPOINT_RENDER
 if(getenv("NF_CAPTURE_HUD_PACKETS"))deferred_capture_hud(index,hud_epoch,hud_refresh);
#endif
}
/* Diagnostic only: retain twelve full 4K RGB frames, write after timed run. */
static uint8_t*deferred_capture_frames;static unsigned deferred_capture_count;
static int deferred_capture_init(void){
 const char*models=getenv("NF_CAPTURE_MIN_MODELS");if(models){char*end;unsigned long value=strtoul(models,&end,10);if(!*models||*end||value<2||value>16||!getenv("NF_CAPTURE_SEQUENCE")||!getenv("NF_CAPTURE_DEFERRED")||getenv("NF_CAPTURE_START_FRAME")||getenv("NF_CAPTURE_ON_UV_ADJUSTMENT"))return 0;deferred_capture_model_trigger=(unsigned)value;deferred_capture_start=216000;}
 const char*trigger=getenv("NF_CAPTURE_ON_UV_ADJUSTMENT");if(trigger){char*end;unsigned long value=strtoul(trigger,&end,10);if(!*trigger||*end||value<1||value>32||!getenv("NF_CAPTURE_SEQUENCE")||!getenv("NF_CAPTURE_DEFERRED")||getenv("NF_CAPTURE_START_FRAME"))return 0;
#ifndef NF_ROAD_ATTRIBUTE_CORRECTION
 return 0;
#endif
 deferred_capture_uv_trigger=(unsigned)value;deferred_capture_start=216000;}
 const char*start=getenv("NF_CAPTURE_START_FRAME");if(start){char*end;unsigned long value=strtoul(start,&end,10);if(!*start||*end||value>216000)return 0;deferred_capture_start=(unsigned)value;}
 if(!getenv("NF_CAPTURE_DEFERRED"))return 1;if(!getenv("NF_CAPTURE_SEQUENCE"))return 0;
 deferred_capture_frames=malloc((size_t)12*3840*2160*3);if(!deferred_capture_frames)return 0;
 memset(deferred_capture_frames,0,(size_t)12*3840*2160*3);return 1;
}
static int deferred_capture_flush(void){
 if((deferred_capture_uv_trigger||deferred_capture_model_trigger)&&deferred_capture_count!=12)return 0;
 int ok=!deferred_native_packet_failed;const char*prefix=getenv("NF_CAPTURE_SEQUENCE");
#ifdef NF_NATIVE_ENDPOINT_RENDER
 const char*hud_prefix=getenv("NF_CAPTURE_HUD_PACKETS");if(hud_prefix){if(deferred_hud_failed)ok=0;for(unsigned i=0;i<12;i++){char path[1200];int n=snprintf(path,sizeof(path),"%s-%03u.hud",hud_prefix,i);FILE*f=n>=0&&(size_t)n<sizeof(path)&&deferred_hud_rows[i]?fopen(path,"wb"):NULL;if(!f)ok=0;else{NFDeferredCaptureSource*s=deferred_capture_sources+i;uint32_t header[4]={0x3148464e,sizeof(NFHudLayerRow),160,s->hud_refresh};if(fwrite(header,1,16,f)!=16||fwrite(&s->epoch,1,8,f)!=8||fwrite(&s->target,1,8,f)!=8||fwrite(deferred_hud_rows[i],sizeof(NFHudLayerRow),160,f)!=160)ok=0;if(fclose(f))ok=0;}free(deferred_hud_rows[i]);deferred_hud_rows[i]=NULL;}}
#endif
 const char*packet_path=getenv("NF_CAPTURE_NATIVE_PACKET");if(packet_path){FILE*f=deferred_native_packet?fopen(packet_path,"wb"):NULL;if(!f)ok=0;else{if(fwrite(deferred_native_packet,1,deferred_native_packet_size,f)!=deferred_native_packet_size)ok=0;if(fclose(f))ok=0;}free(deferred_native_packet);deferred_native_packet=NULL;}
 const char*packet_prefix=getenv("NF_CAPTURE_NATIVE_PACKETS");if(packet_prefix){for(unsigned i=0;i<12;i++){char path[1200];int n=snprintf(path,sizeof(path),"%s-%03u.packet",packet_prefix,i);FILE*f=n>=0&&(size_t)n<sizeof(path)&&deferred_native_packets[i]?fopen(path,"wb"):NULL;if(!f)ok=0;else{if(fwrite(deferred_native_packets[i],1,deferred_native_packet_sizes[i],f)!=deferred_native_packet_sizes[i])ok=0;if(fclose(f))ok=0;}free(deferred_native_packets[i]);deferred_native_packets[i]=NULL;}deferred_native_packets_bytes=0;}
 for(unsigned i=0;i<deferred_capture_count;i++){
  char path[1200];snprintf(path,sizeof(path),"%s-%03u.ppm",prefix,i);FILE*f=fopen(path,"wb");if(!f){ok=0;continue;}
  fprintf(f,"P6\n3840 2160\n255\n");const uint8_t*rgb=deferred_capture_frames+(size_t)i*3840*2160*3;
  for(int y=2159;y>=0;y--)if(fwrite(rgb+(size_t)y*3840*3,3,3840,f)!=3840)ok=0;
  if(fclose(f))ok=0;
 }
 const char*manifest=getenv("NF_CAPTURE_SOURCE_MANIFEST");
 if(manifest){FILE*f=fopen(manifest,"wb");if(!f)ok=0;else{
  if(fprintf(f,"index,epoch,older,newer,capture_ns,rings,near_crossings,alpha,target,older_refresh,newer_refresh,hud_refresh\n")<0)ok=0;
  for(unsigned i=0;i<deferred_capture_source_count;i++){NFDeferredCaptureSource*r=deferred_capture_sources+i;
   if(fprintf(f,"%u,%llu,%llu,%llu,%llu,%llu,%llu,%.15f,%.15f,%u,%u,%u\n",i,(unsigned long long)r->epoch,(unsigned long long)r->older,(unsigned long long)r->newer,(unsigned long long)r->capture_ns,(unsigned long long)r->rings,(unsigned long long)r->crossings,r->alpha,r->target,r->older_refresh,r->newer_refresh,r->hud_refresh)<0)ok=0;
  }if(fclose(f))ok=0;
 }}
 const char*pose_path=getenv("NF_CAPTURE_CAMERA_PAIRS");if(pose_path){FILE*f=fopen(pose_path,"wb");if(!f)ok=0;else{
  if(fprintf(f,"index,role,x,y,z,qx,qy,qz,qw\n")<0)ok=0;
  for(unsigned i=0;i<deferred_capture_source_count;i++)for(unsigned role=0;role<3;role++){NFRigidPose*r=deferred_camera_poses[i]+role;
   if(fprintf(f,"%u,%u,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",i,role,r->position.x,r->position.y,r->position.z,r->rotation.x,r->rotation.y,r->rotation.z,r->rotation.w)<0)ok=0;
  }if(fclose(f))ok=0;
 }}
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 const char*edges=getenv("NF_CAPTURE_ROAD_EDGES");if(edges){FILE*f=fopen(edges,"wb");if(!f)ok=0;else{
  if(fprintf(f,"index,ring,identity,edge,count,shift,height,affine,crossing,z0,z1,a0,a1,b0,b1,offset0,offset1,u,v,world0x,world0y,world0z,world1x,world1y,world1z,camera0x,camera0y,camera0z,camera1x,camera1y,camera1z\n")<0)ok=0;
  for(unsigned i=0;i<deferred_road_edge_count;i++){NFRoadClipEdgeTrace*r=deferred_road_edges+i;
   if(fprintf(f,"%u,%u,%llu,%u,%u,%u,%u,%u,%u,%.17g,%.17g,%d,%d,%d,%d,%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",deferred_road_indices[i],r->ring,(unsigned long long)r->identity,r->edge,r->count,r->shift,r->height,r->affine,r->crossing,r->z0,r->z1,r->attrs[0],r->attrs[1],r->attrs[2],r->attrs[3],r->offsets[0],r->offsets[1],r->u,r->v,r->world0.x,r->world0.y,r->world0.z,r->world1.x,r->world1.y,r->world1.z,r->camera0.x,r->camera0.y,r->camera0.z,r->camera1.x,r->camera1.y,r->camera1.z)<0)ok=0;
  }if(fclose(f))ok=0;
 }}
#endif
 free(deferred_capture_frames);deferred_capture_frames=NULL;return ok;
}
