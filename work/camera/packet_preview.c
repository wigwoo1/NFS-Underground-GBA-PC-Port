#include "road_bundle.h"
/* Offscreen GPU consumer of an acquired, validated scene-packet pair. */
#define main legacy_preview_main
#include "model_preview.c"
#undef main
#include "scene_packet.h"
#ifndef NF_DIAGNOSTIC_PACKET_STAGE
#define NF_DIAGNOSTIC_PACKET_STAGE(stage) ((void)0)
#endif
#ifndef NF_PACKET_NO_FILES
static int enqueue_file(NFSnapshotStore*s,const char*path,NFScenePacket*out){
 FILE*f=fopen(path,"rb");if(!f)return 0;
 if(fseek(f,0,SEEK_END)){fclose(f);return 0;}long n=ftell(f);rewind(f);
 if(n<96||n>64*1024*1024){fclose(f);return 0;}
 void*data=malloc((size_t)n);if(!data){fclose(f);return 0;}
 int ok=fread(data,1,(size_t)n,f)==(size_t)n&&nf_scene_packet_view(data,(size_t)n,out)&&nf_scene_packet_push(s,1,data,(size_t)n);
 fclose(f);free(data);return ok; /* out's metadata only is used after return. */
}
#endif
static const uint8_t* packet_model_identity(const NFScenePacket*p){uint32_t count;memcpy(&count,p->section[1].data+4,4);return p->section[4].data+8+count*20;}
static int packet_endpoint_only;
static unsigned packet_model_endpoint_fallbacks;
static int packet_model_subsets_active;
static unsigned packet_model_subset_frames,packet_model_local_holds,packet_subset_camera_moving;
static int model_subsets_requested(void){const char*v=getenv("NF_CONTINUOUS_MODEL_SETS");return v&&v[0]=='1'&&!v[1];}
static NFTimelineSample packet_presented_time;
static uint32_t packet_source_older_refresh,packet_source_newer_refresh;
static NFRigidPose packet_presented_camera,packet_presented_object;
static NFRigidPose packet_source_cameras[2];
static int packet_continuous_camera;static uint64_t packet_continuous_camera_frames;
static int continuous_camera_requested(void){const char*value=getenv("NF_CONTINUOUS_CAMERA");return value&&value[0]=='1'&&!value[1];}
static void packet_extra_release(void){
 memset(preview_wall_indices,0,sizeof(preview_wall_indices));
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 memset(preview_road_cameras,0,sizeof(preview_road_cameras));memset(preview_road_cameras_present,0,sizeof(preview_road_cameras_present));memset(preview_road_attributes_present,0,sizeof(preview_road_attributes_present));memset(preview_road_attributes,0,sizeof(preview_road_attributes));
#endif
for(unsigned i=0;i<preview_extra_count;i++)free((void*)preview_extra_models[i].data);memset(preview_extra_models,0,sizeof(preview_extra_models));memset(preview_model_indices,0,sizeof(preview_model_indices));memset(preview_world_indices,0,sizeof(preview_world_indices));memset(preview_world_affine,0,sizeof(preview_world_affine));memset(preview_wall_states,0,sizeof(preview_wall_states));memset(preview_wall_planes,0,sizeof(preview_wall_planes));preview_extra_count=0;}
/* Camera is scene-owned, independent of which car occupies model slot zero.
   A changing model set can interpolate it only when every model agrees exactly. */
static int packet_shared_scene_cameras(const NFScenePacket*a,const NFScenePacket*b,NFRigidPose cameras[2]){
 const NFScenePacket*packets[2]={a,b};NFRigidPose candidate[2];
 for(unsigned side=0;side<2;side++){
  unsigned n=nf_scene_packet_model_count(packets[side]);if(!n)return 0;
  for(unsigned i=0;i<n;i++){
   NFSceneSection model;if(!nf_scene_packet_model(packets[side],i,&model))return 0;
   if(!i)memcpy(candidate+side,model.data+48,sizeof(NFRigidPose));
   else if(memcmp(candidate+side,model.data+48,sizeof(NFRigidPose)))return 0;
  }
 }
 memcpy(cameras,candidate,sizeof(candidate));return 1;
}
static int packet_model_pair_indices(const NFScenePacket*a,const NFScenePacket*b,unsigned*out){
 unsigned matched;
 return packet_model_subsets_active?nf_scene_packet_pair_model_subset(a,b,out,16,&matched):nf_scene_packet_pair_model_indices(a,b,out,16);
}
static uint8_t*packet_pair_model(const NFScenePacket*a,const NFScenePacket*b,unsigned older_index,unsigned newer_index,size_t*size){
 if(newer_index==UINT32_MAX){b=a;newer_index=older_index;packet_model_local_holds++;}
 NFSceneSection sa,sb;if(!nf_scene_packet_model(a,older_index,&sa)||!nf_scene_packet_model(b,newer_index,&sb))return NULL;
 const uint8_t*indices_a=NULL,*indices_b=NULL;size_t size_a=0,size_b=0;
 int tagged_a=nf_scene_model_indices(sa,&indices_a,&size_a),tagged_b=nf_scene_model_indices(sb,&indices_b,&size_b);
 if(tagged_a!=tagged_b||(tagged_a&&(!preview_zero_valid||size_a!=size_b||memcmp(indices_a,indices_b,size_a)))){
  if(packet_model_subsets_active&&a!=b){packet_model_local_holds++;return packet_pair_model(a,a,older_index,older_index,size);}return NULL;
 }
 preview_model_indices[older_index]=indices_a;
 const uint8_t*ma=sa.data,*mb=sb.data;uint32_t dimensions[2];memcpy(dimensions,ma+16,8);
 size_t core=sa.size-(tagged_a?16+size_a:0);size_t geometry=core-160-(size_t)dimensions[0]*dimensions[1]*4;
 if(sa.size!=sb.size||memcmp(ma,mb,48)||memcmp(ma+160,mb+160,geometry)||memcmp(packet_model_identity(a)+older_index*20,packet_model_identity(b)+newer_index*20,20)){
  if(packet_model_subsets_active&&a!=b){packet_model_local_holds++;return packet_pair_model(a,a,older_index,older_index,size);}return NULL;
 }
 *size=core+112;uint8_t*model=malloc(*size);if(!model)return NULL;uint32_t magic=0x314d464e;
 memcpy(model,ma,48);memcpy(model,&magic,4);memcpy(model+48,ma+48,56);memcpy(model+104,mb+48,56);memcpy(model+160,ma+104,56);memcpy(model+216,mb+104,56);memcpy(model+272,ma+160,core-160);
 /* Presentation-only: all model/world paths receive the same retained source
    camera endpoints. Native generation, bounds and simulation are unchanged. */
 if(packet_continuous_camera){memcpy(model+48,packet_source_cameras,sizeof(packet_source_cameras));}
 return model;
}
static int(*packet_background_pair)(const NFScenePacket*,const NFScenePacket*,const NFTimelineSample*);
static int render_packet_views(NFScenePacket,NFScenePacket,NFTimelineSample,char**);
static int render_packet_at(NFSnapshotStore*s,double target,char**argv){
 NF_DIAGNOSTIC_PACKET_STAGE(0);
 NFScenePacket a,b;NFSnapshotPair pair;
 if(nf_snapshot_acquire(s,target,0,&pair)!=NF_TIME_READY||!nf_scene_packet_view(pair.older,pair.older_size,&a)||!nf_scene_packet_view(pair.newer,pair.newer_size,&b)){nf_snapshot_release(s);return 23;}
 NF_DIAGNOSTIC_PACKET_STAGE(1);
 if(packet_endpoint_only){b=a;pair.time.alpha=0;}
 packet_model_subsets_active=0;
 unsigned model_pair[16];
 if(!nf_scene_packet_pair_model_indices(&a,&b,model_pair,16)){
  unsigned matched=0;
  if(model_subsets_requested()&&continuous_camera_requested()&&
     nf_scene_packet_pair_model_subset(&a,&b,model_pair,16,&matched)&&matched&&
     packet_shared_scene_cameras(&a,&b,packet_source_cameras)){
   packet_model_subsets_active=1;packet_model_subset_frames++;
   if(pair.time.alpha>0&&pair.time.alpha<1&&memcmp(packet_source_cameras,packet_source_cameras+1,sizeof(NFRigidPose)))packet_subset_camera_moving++;
  }else{
   packet_model_endpoint_fallbacks++;b=a;pair.time.alpha=0;
   if(!nf_scene_packet_pair_model_indices(&a,&b,model_pair,16)){nf_snapshot_release(s);return 24;}
  }
 }
packet_source_older_refresh=a.end_refresh;packet_source_newer_refresh=b.end_refresh;
 packet_continuous_camera=continuous_camera_requested();
 if(!packet_model_subsets_active&&(getenv("NF_CAPTURE_CAMERA_PAIRS")||packet_continuous_camera)){NFSceneSection model_a,model_b;
  if(!nf_scene_packet_model(&a,0,&model_a)||!nf_scene_packet_model(&b,model_pair[0],&model_b)){nf_snapshot_release(s);return 24;}
  memcpy(packet_source_cameras,model_a.data+48,sizeof(NFRigidPose));memcpy(packet_source_cameras+1,model_b.data+48,sizeof(NFRigidPose));
 }
#ifdef NF_DIAGNOSTIC_PAIR_PREPARE
 int prepared=NF_DIAGNOSTIC_PAIR_PREPARE(&a,&b,&pair.time);if(!prepared){nf_snapshot_release(s);return 24;}
#endif
 if(packet_background_pair&&!packet_background_pair(&a,&b,&pair.time)){packet_model_subsets_active=0;nf_snapshot_release(s);return 48;}
 int result=render_packet_views(a,b,pair.time,argv);packet_model_subsets_active=0;nf_snapshot_release(s);return result;
}
/* Consumes immutable views only. No snapshot acquisition, capture or bridge calls. */
static int render_packet_views(NFScenePacket a,NFScenePacket b,NFTimelineSample time,char**argv){
 NFSnapshotStore*s=NULL;NFSnapshotPair pair={0};pair.time=time;
 NF_DIAGNOSTIC_PACKET_STAGE(2);
 unsigned models=nf_scene_packet_model_count(&a),model_pair[16];
 if(!packet_model_pair_indices(&a,&b,model_pair)){packet_extra_release();nf_snapshot_release(s);return 24;}
 unsigned world_count;memcpy(&world_count,a.section[1].data+4,4);
 NFWorldMetadata wa[128];unsigned ca;
 if(!nf_scene_world_metadata_all(a.section[1],wa,128,&ca)||ca!=world_count){packet_extra_release();nf_snapshot_release(s);return 43;}
 /* World visibility sets may change from one game refresh to the next. Compute
    identity correspondence, then draw the complete older endpoint as one
    internally consistent scene. The correspondence is not yet used to
    interpolate world geometry. */
 unsigned world_pair[128],world_matched=0;
 if(!nf_scene_packet_pair_world_indices(&a,&b,world_pair,128,&world_matched)||world_matched>world_count){packet_extra_release();nf_snapshot_release(s);return 43;}
 if(preview_display_palette_valid){
  for(unsigned i=0;i<ca;i++){uint32_t kind;memcpy(&kind,a.section[4].data+8+i*20,4);unsigned mode=wa[i].mode;
   if((kind==1&&(mode!=1&&mode!=4&&mode!=5&&mode!=6))||(kind==2&&(mode!=7&&mode!=8))||(kind!=1&&kind!=2)){packet_extra_release();nf_snapshot_release(s);return 43;}
  }
  unsigned n=nf_scene_packet_model_count(&a);if(!n||(!packet_model_subsets_active&&n!=nf_scene_packet_model_count(&b))){packet_extra_release();nf_snapshot_release(s);return 43;}
  for(unsigned i=0;i<n;i++){NFSceneSection ma,mb;const uint8_t*ia,*ib;size_t na,nb;
   if(!nf_scene_packet_model(&a,i,&ma)||!nf_scene_packet_model(model_pair[i]==UINT32_MAX?&a:&b,model_pair[i]==UINT32_MAX?i:model_pair[i],&mb)||!nf_scene_model_indices(ma,&ia,&na)||!nf_scene_model_indices(mb,&ib,&nb)){packet_extra_release();nf_snapshot_release(s);return 43;}
  }
 }
 for(unsigned i=0;i<world_count;i++){
  if(wa[i].mode==1||wa[i].mode==4){uint32_t kind;memcpy(&kind,a.section[4].data+8+i*20,4);if(kind!=1){packet_extra_release();nf_snapshot_release(s);return 41;}preview_world_indices[i]=wa[i].data;preview_world_affine[i]=wa[i].mode==4;}
  #ifdef NF_ROAD_ATTRIBUTE_CORRECTION
  else if(wa[i].mode==5||wa[i].mode==6||wa[i].mode==9||wa[i].mode==10){
   /* metadata_all already validated every payload and raw attribute against
      its world surface. Reuse that span instead of rescanning all surfaces
      for every road; copy raw attributes before releasing the packet. */
   if(!preview_road_table_load()||wa[i].size<sizeof(NFRoadSourceAttributes)){packet_extra_release();nf_snapshot_release(s);return 41;}
   if(!nf_preview_road_metadata(wa+i,preview_road_attributes+i,preview_road_cameras+i,preview_road_cameras_present+i,preview_world_affine+i)){packet_extra_release();nf_snapshot_release(s);return 41;}
   preview_road_attributes_present[i]=1;preview_world_indices[i]=wa[i].data;/* mapping copied by metadata helper */
  }
#endif
  else if(wa[i].mode==2||wa[i].mode==3){preview_wall_states[i]=wa[i].data;preview_wall_planes[i]=wa[i].mode==3?17:1;}
  else if(wa[i].mode==7||wa[i].mode==8){if(!preview_display_palette_valid){packet_extra_release();nf_snapshot_release(s);return 43;}preview_wall_states[i]=wa[i].data;preview_wall_indices[i]=wa[i].data+wa[i].size/2;preview_wall_planes[i]=wa[i].mode==8?17:1;}
  else if(wa[i].mode){packet_extra_release();nf_snapshot_release(s);return 41;}
 }
 NF_DIAGNOSTIC_PACKET_STAGE(3);
 NFSceneSection primary_a,primary_b;if(!nf_scene_packet_model(&a,0,&primary_a)||!nf_scene_packet_model(model_pair[0]==UINT32_MAX?&a:&b,model_pair[0]==UINT32_MAX?0:model_pair[0],&primary_b)){packet_extra_release();nf_snapshot_release(s);return 24;}const uint8_t*ma=primary_a.data,*mb=primary_b.data;
 size_t model_size;uint8_t*model=packet_pair_model(&a,&b,0,model_pair[0],&model_size);if(!model){packet_extra_release();nf_snapshot_release(s);return 24;}
 for(unsigned i=1;i<models;i++){size_t extra_size;uint8_t*extra=packet_pair_model(&a,&b,i,model_pair[i],&extra_size);if(!extra){packet_extra_release();free(model);nf_snapshot_release(s);return 24;}preview_extra_models[preview_extra_count++]=(PreviewMemory){extra,extra_size};}
 preview_memory[0]=(PreviewMemory){model,model_size};uint32_t empty[2]={0x31574650,0};preview_memory[1]=(PreviewMemory){(const uint8_t*)empty,8};
 for(unsigned i=1;i<=3;i++)preview_memory[i+1]=(PreviewMemory){a.section[i].data,a.section[i].size};
 preview_alpha_override=pair.time.alpha;
 packet_presented_time=pair.time;
 NFRigidPose camera_a,camera_b,object_a,object_b;
 memcpy(&camera_a,model+48,sizeof(camera_a));memcpy(&camera_b,model+104,sizeof(camera_b));memcpy(&object_a,ma+104,sizeof(object_a));memcpy(&object_b,mb+104,sizeof(object_b));
 if(!nf_pose_sample(&camera_a,&camera_b,pair.time.alpha,&packet_presented_camera)||!nf_pose_sample(&object_a,&object_b,pair.time.alpha,&packet_presented_object)){packet_extra_release();free(model);memset(preview_memory,0,sizeof(preview_memory));nf_snapshot_release(s);return 28;}
 if(!preview_measure_only)printf("packet older=%llu newer=%llu alpha=%.6f target=%.6f\n",(unsigned long long)pair.time.older,(unsigned long long)pair.time.newer,pair.time.alpha,pair.time.target);
 NF_DIAGNOSTIC_PACKET_STAGE(4);
 char*args[]={argv[0],"packet-model",argv[3],"packet-wireframe","packet-world","packet-order","packet-lighting"};
#ifdef NF_DIAGNOSTIC_PACKET_SELECT
 NF_DIAGNOSTIC_PACKET_SELECT(&a);
#endif
#ifdef NF_DIAGNOSTIC_PAIR_SELECT
 NF_DIAGNOSTIC_PAIR_SELECT(&a,&b);
#endif
 NF_DIAGNOSTIC_PACKET_STAGE(5);
 int result=legacy_preview_main(7,args);NF_DIAGNOSTIC_PACKET_STAGE(6);memset(preview_memory,0,sizeof(preview_memory));packet_extra_release();free(model);
 if(!result&&packet_continuous_camera)packet_continuous_camera_frames++;
#ifdef NF_DIAGNOSTIC_FRAME_RELEASE
 NF_DIAGNOSTIC_FRAME_RELEASE();
#endif
 nf_snapshot_release(s);NF_DIAGNOSTIC_PACKET_STAGE(7);return result;
}
#include "ordered_bundle.h"
#include "indexed_copy_gpu.h"
static const NFOrderedBundle*packet_ordered_bundle;
static const NFRoadBundle*packet_road_bundle;
static NFRoadAssetView packet_road_material;
static unsigned packet_road_cursor,packet_road_matches;
static int packet_road_valid;
static unsigned packet_road_right;
#include "road_edge_gpu.h"
static int packet_road_after(unsigned command){return !packet_road_valid||road_edge_gpu_draw(&packet_road_material,packet_road_right);}
static unsigned packet_ordered_cursor,packet_ordered_draws,packet_ordered_geometry;
static PreviewScissor packet_ordered_saved_scissor;
static int packet_ordered_2d(void){
 while(packet_ordered_cursor<packet_ordered_bundle->event_count){
  NFOrderedSceneEvent e;memcpy(&e,packet_ordered_bundle->events+packet_ordered_cursor*32,32);if(e.type>=3)break;
  const uint8_t*entry=packet_ordered_bundle->directory+e.ordinal*8;unsigned offset=nf_bundle_word(entry),size=nf_bundle_word(entry+4);
  if(!indexed_copy_gpu_draw(packet_ordered_bundle->data+offset,size))return 0;
  packet_ordered_cursor++;packet_ordered_draws++;
 }return 1;
}
static int packet_ordered_before(unsigned command){
 if(!command){packet_road_cursor=packet_road_matches=0;packet_road_valid=0;packet_ordered_saved_scissor=preview_scissor_save();packet_ordered_cursor=packet_ordered_draws=packet_ordered_geometry=0;}
 if(!command&&packet_road_bundle&&packet_road_bundle->baseline&&!indexed_copy_gpu_draw(packet_road_bundle->baseline,packet_road_bundle->baseline_size))return 0;
 if(!packet_ordered_2d()||packet_ordered_cursor>=packet_ordered_bundle->event_count)return 0;
 NFOrderedSceneEvent e;memcpy(&e,packet_ordered_bundle->events+packet_ordered_cursor*32,32);if(e.type<3||command!=packet_ordered_geometry)return 0;
 packet_road_valid=0;
 if(packet_road_bundle&&packet_road_cursor<packet_road_bundle->count){
  const uint8_t*entry=packet_road_bundle->directory+packet_road_cursor*16;uint32_t pass=nf_bundle_word(entry),ordinal=nf_bundle_word(entry+4);
  if(pass==e.pass&&ordinal==e.ordinal){
   if(e.type!=3||e.kind!=1||!nf_road_asset_view(packet_road_bundle->data+nf_bundle_word(entry+8),nf_bundle_word(entry+12),&packet_road_material))return 0;
   packet_road_valid=1;packet_road_cursor++;packet_road_matches++;
  }
 }
  unsigned index=nf_bundle_word(packet_ordered_bundle->packet.section[2].data+8+command*4),world=nf_bundle_word(packet_ordered_bundle->packet.section[1].data+4);const uint8_t*bounds=NULL;double alpha;
 if(index>=UINT32_MAX-15){if(!nf_scene_packet_model_bounds(&packet_ordered_bundle->packet,&bounds))return 0;bounds+=(UINT32_MAX-index)*8;}
 else{if(index>=world||!nf_scene_packet_bounds(&packet_ordered_bundle->packet,&alpha,&bounds))return 0;bounds+=index*8;}
 uint16_t clip[4];memcpy(clip,bounds,8);packet_road_right=clip[1];
 int left=300+(int)ceil(clip[0]*13.5-.5),right=300+(int)ceil(clip[1]*13.5-.5),top=(int)ceil(clip[2]*13.5-.5),bottom=(int)ceil(clip[3]*13.5-.5);
 glEnable(GL_SCISSOR_TEST);glScissor(left,2160-bottom,right-left,bottom-top);
 packet_ordered_cursor++;packet_ordered_geometry++;return 1;
}
static int packet_ordered_after(void){preview_scissor_restore(&packet_ordered_saved_scissor);packet_road_valid=0;return packet_ordered_2d()&&packet_ordered_cursor==packet_ordered_bundle->event_count&&(!packet_road_bundle||packet_road_cursor==packet_road_bundle->count);}
static int render_ordered_bundle(const void*data,size_t size,char**argv){
 NFOrderedBundle bundle;if(!nf_ordered_bundle_view(data,size,&bundle)||!preview_display_palette_valid||!preview_zero_valid)return 44;
 NFRigidPose cameras[144];memcpy(cameras,bundle.cameras,bundle.camera_count*sizeof(*cameras));
 const NFRigidPose*saved_cameras=preview_command_cameras;unsigned saved_count=preview_command_camera_count;
 if(preview_before_command||preview_after_commands||packet_ordered_bundle)return 44;
 preview_command_cameras=cameras;preview_command_camera_count=bundle.camera_count;packet_ordered_bundle=&bundle;
 preview_before_command=packet_ordered_before;preview_after_commands=packet_ordered_after;
 NFTimelineSample time={0};time.older=time.newer=bundle.packet.serial;time.alpha=0;
 int result=render_packet_views(bundle.packet,bundle.packet,time,argv);
 preview_before_command=NULL;preview_after_commands=NULL;packet_ordered_bundle=NULL;preview_command_cameras=saved_cameras;preview_command_camera_count=saved_count;
 return result;
}
static int render_road_bundle(const void*data,size_t size,char**argv){
 NFRoadBundle bundle;if(packet_road_bundle||preview_after_command||!nf_road_bundle_view(data,size,&bundle))return 44;
 packet_road_bundle=&bundle;preview_after_command=packet_road_after;int result=render_ordered_bundle(bundle.ordered.data,bundle.ordered.size,argv);packet_road_bundle=NULL;preview_after_command=NULL;packet_road_valid=0;return result;
}
#include "road_split_gpu.h"
#ifndef NF_PACKET_NO_MAIN
static int compare_ms(const void*a,const void*b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
int main(int argc,char**argv){
 if(argc!=4&&argc!=5)return 1;
 int sequence=argc==5&&!strcmp(argv[4],"--phases"),benchmark=argc==5&&!strcmp(argv[4],"--benchmark");if(argc==5&&!sequence&&!benchmark)return 1;
 const char*phase=getenv("NF_PREVIEW_PHASE");if(!phase)phase="2";
 char*end;long index=strtol(phase,&end,10);if(!*phase||*end||index<0||index>4)return 21;
 const char*fraction=getenv("NF_PREVIEW_FRACTION");double fraction_value=0;
 if(fraction){fraction_value=strtod(fraction,&end);if(!*fraction||*end||!isfinite(fraction_value)||fraction_value<0||fraction_value>1||benchmark||sequence)return 21;}
 NFSnapshotStore*s=nf_snapshot_create(128*1024*1024);NFScenePacket first,last;
 if(!s||!enqueue_file(s,argv[1],&first)||!enqueue_file(s,argv[2],&last)){nf_snapshot_destroy(s);return 22;}
 preview_keep_context=1;preview_measure_only=benchmark;int result=0;double durations[300];unsigned measured=0;LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);
 for(int iteration=0;iteration<(benchmark?320:sequence?5:1);iteration++){
  int i=benchmark?iteration%5:sequence?iteration:(int)index;
  char setting[32];snprintf(setting,sizeof(setting),"NF_PREVIEW_PHASE=%d",i);_putenv(setting);
  double target=first.end_refresh+(last.end_refresh-first.end_refresh)*(fraction?fraction_value:i/4.);
  LARGE_INTEGER begin,finish;QueryPerformanceCounter(&begin);result=render_packet_at(s,target,argv);QueryPerformanceCounter(&finish);if(result)break;
  if(benchmark&&iteration>=20)durations[measured++]=(finish.QuadPart-begin.QuadPart)*1000.0/frequency.QuadPart;
  if(!benchmark)printf("resources contexts=%u uploads=%u hits=%u bytes=%llu\n",preview_contexts,preview_uploads,preview_hits,(unsigned long long)preview_texture_bytes);
 }
 if(benchmark&&!result&&measured==300){
  char path[1024];snprintf(path,sizeof(path),"%s.csv",argv[3]);FILE*f=fopen(path,"wb");if(!f)result=27;
  double total=0;unsigned over=0;for(unsigned i=0;i<measured;i++){total+=durations[i];over+=durations[i]>1000.0/60;if(f)fprintf(f,"%u,%.6f\n",i,durations[i]);}if(f)fclose(f);
  qsort(durations,measured,sizeof(double),compare_ms);
  printf("renderer=%s\nframes=%u mean_ms=%.6f p50_ms=%.6f p95_ms=%.6f max_ms=%.6f over_60hz_budget=%u\ncontexts=%u uploads=%u hits=%u lighting_fallbacks=%u\n",glGetString(GL_RENDERER),measured,total/measured,durations[149],durations[284],durations[299],over,preview_contexts,preview_uploads,preview_hits,lighting_fallback);
 }
 preview_shutdown();nf_snapshot_release(s);nf_snapshot_destroy(s);return result;
}
#endif





