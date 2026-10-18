/* Offscreen replay verifies actual GPU-consumer pose assembly on captured
   membership transitions. It does not run game logic or validate display pacing. */
#include "scene_packet.h"
#include "rigid_motion.h"
static void subset_verify_models(const NFScenePacket*,const NFScenePacket*);
#define NF_DIAGNOSTIC_PAIR_SELECT subset_verify_models
#define NF_PACKET_NO_MAIN
#define NF_PACKET_NO_FILES
#include "packet_preview.c"
static unsigned verified_models,verification_failed;
static int test_mesh_change;
static void subset_verify_models(const NFScenePacket*a,const NFScenePacket*b){
 unsigned n=nf_scene_packet_model_count(a),map[16],matched;
 if(!nf_scene_packet_pair_model_subset(a,b,map,16,&matched)){verification_failed++;return;}
 NFSceneSection first_a,first_b;
 if(!nf_scene_packet_model(a,0,&first_a)||!nf_scene_packet_model(b,0,&first_b)){verification_failed++;return;}
 if(preview_extra_count!=n-1){verification_failed++;return;}
 for(unsigned i=0;i<n;i++){
  NFSceneSection old,new;
  if(!nf_scene_packet_model(a,i,&old)||!nf_scene_packet_model(map[i]==UINT32_MAX?a:b,map[i]==UINT32_MAX?i:map[i],&new)){verification_failed++;return;}
  if(test_mesh_change&&map[i]==0)new=old;
  const uint8_t*built=i?preview_extra_models[i-1].data:preview_memory[0].data;
  if(!built||memcmp(built+48,first_a.data+48,56)||memcmp(built+104,first_b.data+48,56)||
     memcmp(built+160,old.data+104,56)||memcmp(built+216,new.data+104,56)){verification_failed++;return;}
  verified_models++;
 }
}
static void*read_packet(const char*path,size_t*size){
 FILE*f=fopen(path,"rb");if(!f)return NULL;
 if(fseek(f,0,SEEK_END)){fclose(f);return NULL;}long n=ftell(f);rewind(f);
 void*data=n>=96&&n<=64*1024*1024?malloc((size_t)n):NULL;
 if(!data||fread(data,1,n,f)!=(size_t)n){free(data);fclose(f);return NULL;}
 fclose(f);*size=n;return data;
}
int main(int argc,char**argv){
 if(argc!=3&&argc!=4)return 1;
 int conflict=argc==4&&!strcmp(argv[3],"--conflicting-camera");
 int missing=argc==4&&!strcmp(argv[3],"--unmatched-models");
 test_mesh_change=argc==4&&!strcmp(argv[3],"--changed-mesh");
 if(argc==4&&!conflict&&!missing&&!test_mesh_change)return 1;
 int fallback=conflict||missing;
 size_t sizes[2];void*data[2]={read_packet(argv[1],sizes),read_packet(argv[2],sizes+1)};
 NFScenePacket a,b;
 if(!data[0]||!data[1]||!nf_scene_packet_view(data[0],sizes[0],&a)||!nf_scene_packet_view(data[1],sizes[1],&b))return 2;
 if(conflict){
  NFSceneSection model;if(nf_scene_packet_model_count(&b)<2||!nf_scene_packet_model(&b,1,&model))return 3;
  double x;memcpy(&x,model.data+48,8);x+=1;memcpy((void*)(model.data+48),&x,8);
  if(!nf_scene_packet_view(data[1],sizes[1],&b))return 3;
 }
 if(missing){
  unsigned world;memcpy(&world,b.section[1].data+4,4);
  for(unsigned i=0;i<nf_scene_packet_model_count(&b);i++){
   uint8_t*id=(uint8_t*)b.section[4].data+8+(world+i)*20+8;uint32_t value;memcpy(&value,id,4);value^=0x40000000;memcpy(id,&value,4);
  }
  if(!nf_scene_packet_view(data[1],sizes[1],&b))return 3;
 }
 if(test_mesh_change){
  NFSceneSection model;if(!nf_scene_packet_model(&b,0,&model))return 3;
  double vertex;memcpy(&vertex,model.data+160,8);vertex+=1;memcpy((void*)(model.data+160),&vertex,8);
  if(!nf_scene_packet_view(data[1],sizes[1],&b))return 3;
 }
 NFSnapshotStore*store=nf_snapshot_create(sizes[0]+sizes[1]+1024);
 if(!store||!nf_scene_packet_push(store,1,data[0],sizes[0])||!nf_scene_packet_push(store,1,data[1],sizes[1]))return 4;
 _putenv("NF_CONTINUOUS_CAMERA=1");_putenv("NF_CONTINUOUS_MODEL_SETS=1");_putenv("NF_PREVIEW_PHASE=0");
 preview_keep_context=1;preview_measure_only=1;
 char*args[]={argv[0],"unused","unused","subset-replay","unused","unused","unused"};
 int result=0;
 for(unsigned phase=1;phase<=3;phase++){
  double fraction=phase/4.0,target=a.end_refresh+(b.end_refresh-a.end_refresh)*fraction;
  result=render_packet_at(store,target,args);if(result)break;
  double expected=fallback?0:fraction;
  if(fabs(packet_presented_time.alpha-expected)>1e-9){result=60;break;}
  NFSceneSection old,new;nf_scene_packet_model(&a,0,&old);nf_scene_packet_model(&b,0,&new);
  NFRigidPose start,end,sampled;memcpy(&start,old.data+48,56);memcpy(&end,fallback?old.data+48:new.data+48,56);
  if(!nf_pose_sample(&start,&end,expected,&sampled)){result=61;break;}
  const double*x=(const double*)&sampled,*y=(const double*)&packet_presented_camera;
  for(unsigned i=0;i<7;i++)if(fabs(x[i]-y[i])>1e-9){result=62;break;}
  if(result||verification_failed){if(!result)result=63;break;}
 }
 if(!result&&((!fallback&&(packet_model_subset_frames!=3||packet_model_endpoint_fallbacks))||
    (fallback&&(packet_model_subset_frames||packet_model_endpoint_fallbacks!=3))))result=64;
 if(!result&&test_mesh_change&&packet_model_local_holds!=6)result=65;
 printf("{\"result\":%d,\"subset_frames\":%u,\"endpoint_fallbacks\":%u,\"local_holds\":%u,\"verified_models\":%u,\"camera_conflict\":%s}\n",
 result,packet_model_subset_frames,packet_model_endpoint_fallbacks,packet_model_local_holds,verified_models,conflict?"true":"false");
 preview_shutdown();nf_snapshot_release(store);nf_snapshot_destroy(store);free(data[0]);free(data[1]);return result;
}
