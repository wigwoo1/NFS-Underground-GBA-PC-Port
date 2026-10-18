#include "scene_segments.h"
#define NF_PACKET_NO_MAIN
#define NF_PACKET_NO_FILES
#include "scene_packet.h"
static void live_clip_select(const NFScenePacket*);
static void live_clip_surface(int);
static void live_clip_pair(const NFScenePacket*,const NFScenePacket*);
static void live_frame_release(void);
#define NF_DIAGNOSTIC_FRAME_RELEASE live_frame_release
#define NF_DIAGNOSTIC_PAIR_SELECT live_clip_pair
#define NF_DIAGNOSTIC_PACKET_SELECT live_clip_select
#define NF_DIAGNOSTIC_SURFACE_CLIP live_clip_surface
#include "packet_preview.c"
typedef struct {uint32_t serial,begin,end,count,kind[256];uint16_t bounds[256][4];int valid;} LiveClips;
static LiveClips live_clips[16],*active_clips;static uint64_t clip_epoch;static unsigned clip_cursor;
static int clip_enabled;
static void* entrant_frame;
static LiveClips entrant_clips;
static unsigned entrant_applied,entrant_released;
static void live_frame_release(void){
 if(!entrant_frame)return;
 const char*prefix=getenv("NF_ENTRANT_LIVE_CAPTURE");
 if(prefix){
  uint8_t*pixels=malloc(3840*2160*3);char path[1200];
  snprintf(path,sizeof(path),"%s-e%llu-s%u-a%.9f.ppm",prefix,(unsigned long long)clip_epoch,entrant_clips.serial,packet_presented_time.alpha);
  FILE*f=pixels?fopen(path,"wb"):NULL;
  if(f){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,pixels);fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)fwrite(pixels+y*3840*3,3,3840,f);fclose(f);}
  else fprintf(stderr,"entrant capture failed: %s\n",path);
  free(pixels);
 }
 nf_scene_packet_free(entrant_frame);entrant_frame=NULL;entrant_released++;
}

static int(*read_bounds)(uint64_t,uint32_t,uint32_t,uint32_t,unsigned,uint16_t*);
static int(*read_pose)(uint64_t,uint32_t,uint32_t,uint32_t,void*);
static unsigned pose_available,pose_expired;
static int sampled_enabled;
static int(*sample_pose)(const void*,const void*,double,void*);
static int(*sample_bounds)(uint64_t,uint32_t,uint32_t,uint32_t,const void*,uint16_t*,unsigned,unsigned*);
static unsigned sampled_applied,sampled_unavailable,sampled_entrants;
static int(*sample_queue)(uint64_t,uint32_t,uint32_t,uint32_t,const void*,void*);
static int(*extract_candidate)(uint64_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,void**,size_t*);
static void(*free_candidate)(void*);
static int(*read_dispatch)(uint64_t,uint32_t,uint32_t,uint32_t,uint32_t*,unsigned,unsigned*);
static int(*read_snapshot)(uint64_t,uint32_t,uint32_t,uint32_t,uint32_t,void*,size_t);
static int(*read_regions)(uint64_t,uint32_t,uint32_t,uint32_t,uint32_t*,unsigned,unsigned*);
static int(*read_origin)(uint64_t,uint32_t,uint32_t,uint32_t,unsigned,uint32_t*);
static int(*read_wall_pass)(uint64_t,uint32_t,uint32_t,uint32_t,unsigned,uint32_t*);
static int segment_anchor(const NFScenePacket*a,uint32_t commands[257][6],unsigned command_count,const uint8_t*plan,unsigned anchor,uint32_t source,uint32_t state,uint32_t descriptor){
 uint32_t rows[256][9],origins[257][12]={{0}},passes[257][3]={{0}},sampled[64];unsigned calls=0,count=0,n;
 if(!read_regions(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,&rows[0][0],256,&calls))return 0;
 for(unsigned j=0;j<command_count;j++)if(commands[j][0]!=3){
  if(!read_origin(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,commands[j][1],origins[j]))return 0;
  if(commands[j][0]==2&&!read_wall_pass(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,commands[j][1],passes[j]))return 0;
 }
 memcpy(&n,plan,4);if(n>64)return 0;
 for(unsigned j=0;j<n;j++){uint32_t draw[2];memcpy(draw,plan+20+j*32,8);if(!draw[1])sampled[count++]=draw[0];}
 uint8_t desc[48];uint32_t vertex_base;uint16_t first,total,region;
 if(!read_snapshot(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,state+16,&vertex_base,4)||!read_snapshot(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,descriptor,desc,48))return 0;
 memcpy(&first,desc,2);memcpy(&total,desc+2,2);memcpy(&region,plan+4,2);
 uint64_t start=(uint64_t)vertex_base+(uint64_t)first*68,end=start+(uint64_t)total*68;
 if(!total||total>32||end>0x100000000ull||source<start||(uint64_t)source+68>end||(source-start)%68)return 0;
 const char*fault=getenv("NF_ENTRANT_FAULT");if(fault&&!strcmp(fault,"region-conflict"))region^=1;
 NFSceneSegments segments;NFWallInsertions insertions;
 if(!nf_scene_segments(&rows[0][0],calls,&commands[0][0],command_count,&origins[0][0],&passes[0][0],&segments))return 0;
 for(unsigned j=0;j<segments.count;j++){
  NFSceneSegment*seg=&segments.segments[j];if(seg->kind!=1||anchor<seg->begin||anchor>=seg->end)continue;
  unsigned owner=UINT32_MAX,occurrences=0;
  for(unsigned c=0;c<calls;c++){
   if((rows[c][0]&65535)==region&&rows[c][8]==0&&rows[c][5]==0)occurrences++;
   if(segments.offsets[c]<=j&&j<segments.offsets[c+1])owner=c;
  }
  if(owner==UINT32_MAX||occurrences!=1||(rows[owner][0]&65535)!=region||rows[owner][8]!=0||rows[owner][5]!=0)return 0;
  if(!nf_segment_wall_insertions(&rows[0][0],calls,&commands[0][0],command_count,&origins[0][0],&passes[0][0],j,sampled,count,&insertions))return 0;
  return insertions.count==1&&insertions.source[0]==source&&insertions.before[0]==anchor;
 }
 return 0;
}
static void audit_entrants(const NFScenePacket*a,const NFScenePacket*b,const uint32_t pose[26]){
 uint8_t batch[4+NF_VISIBILITY_QUEUE_CAPACITY*2068];uint32_t count,commands[257][6];unsigned command_count=0;
 if(!read_dispatch(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,&commands[0][0],257,&command_count))return;
 if(!sample_queue(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,pose,batch))return;
 memcpy(&count,batch,4);if(count>NF_VISIBILITY_QUEUE_CAPACITY)return;
 for(unsigned q=0;q<count;q++){
  const uint8_t*p=batch+4+q*2068;uint32_t n;memcpy(&n,p,4);if(n>64)return;
  for(unsigned k=0;k<n;k++){
   uint32_t draw[8];memcpy(draw,p+20+k*32,32);int found=0;uint32_t state=0;
   for(unsigned i=0;i<active_clips->count;i++){uint32_t id[5];memcpy(id,a->section[4].data+8+i*20,20);if(id[0]==2&&id[2]==draw[0])found=1;}
   if(found)continue;
   unsigned anchor=UINT32_MAX;uint32_t descriptor=0;int ambiguous=0;
   /* A source-only peer match is valid only for a unique occurrence. */
   unsigned previous_command=0;int have_previous=0;
   /* Recover descriptor from retained peers in this sampled first-pass region. */
   for(unsigned t=0;t<n;t++){
    uint32_t peer[2];memcpy(peer,p+20+t*32,8);if(peer[1])continue;
    unsigned matches=0,matched=0,sampled_matches=0;
    for(unsigned u=0;u<n;u++){uint32_t source;memcpy(&source,p+20+u*32,4);if(source==peer[0])sampled_matches++;}
    for(unsigned j=0;j<command_count;j++)if(commands[j][0]==2&&commands[j][2]==peer[0]){matches++;matched=j;}
    const char*peer_fault=getenv("NF_ENTRANT_FAULT");
    if(matches&&peer_fault&&!strcmp(peer_fault,"duplicate-peer"))matches++;
    if(matches>1||sampled_matches!=1){ambiguous=1;continue;}
    if(!matches)continue;
    unsigned j=matched;
    if(commands[j][5]){ambiguous=1;continue;}
    if(have_previous&&j<=previous_command){ambiguous=1;continue;}
    previous_command=j;have_previous=1;
    {
     if(descriptor&&descriptor!=commands[j][4])ambiguous=1;
     descriptor=commands[j][4];
     /* Bind state through this command's packet occurrence, never unrelated walls. */
     uint32_t index,id[5];
     memcpy(&index,a->section[2].data+8+j*4,4);
     if(index>=active_clips->count){ambiguous=1;continue;}
     memcpy(id,a->section[4].data+8+index*20,20);
     if(id[0]!=2||id[2]!=peer[0]||!id[1]){ambiguous=1;continue;}
     if(state&&state!=id[1])ambiguous=1;
     state=id[1];
     if(peer[0]>draw[0]&&(anchor==UINT32_MAX||j<anchor))anchor=j;
    }
   }
   if(anchor==UINT32_MAX&&descriptor)for(unsigned j=0;j<command_count;j++)if(commands[j][0]==1&&commands[j][4]==descriptor){if(anchor!=UINT32_MAX)ambiguous=1;anchor=j;}
   if(!ambiguous&&anchor<command_count&&!segment_anchor(a,commands,command_count,p,anchor,draw[0],state,descriptor))ambiguous=1;
   const char*state_fault=getenv("NF_ENTRANT_FAULT");
   if(state_fault&&!strcmp(state_fault,"state-conflict"))ambiguous=1;
   printf("entrant_state scene=%u state=%u accepted=%d\n",a->serial,state,state&&!ambiguous);
   printf("entrant_anchor scene=%u source=%u command=%u kind=%u descriptor=%u ambiguous=%d\n",a->serial,draw[0],anchor,anchor<command_count?commands[anchor][0]:0,descriptor,ambiguous);
   uint32_t next[257][6];unsigned next_count=0;int verified=0;
   if(anchor<command_count&&read_dispatch(clip_epoch,b->serial,b->begin_refresh,b->end_refresh,&next[0][0],257,&next_count))for(unsigned j=0;j+1<next_count;j++)if(next[j][0]==2&&next[j][2]==draw[0]&&next[j+1][0]==commands[anchor][0]&&next[j+1][2]==commands[anchor][2])verified=1;
   printf("entrant_anchor_reference scene=%u source=%u adjacent_match=%d\n",a->serial,draw[0],verified);
   void*surface=NULL;size_t bytes=0;int ok=state&&!ambiguous&&extract_candidate(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,state,draw[0],&surface,&bytes);
   printf("entrant_asset scene=%u source=%u pass=%u flags=%u extracted=%d bytes=%llu\n",a->serial,draw[0],draw[1],draw[7],ok,(unsigned long long)bytes);
   const char*prefix=getenv("NF_ENTRANT_EXPORT");
   if((prefix||getenv("NF_LIVE_ENTRANTS"))&&ok&&!ambiguous&&anchor<command_count&&commands[anchor][0]==2&&!draw[1]){
    uint16_t base=0;void*original=NULL,*expanded=NULL;size_t original_bytes=0,expanded_bytes=0;
    int composed=read_snapshot(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,draw[0]+44,&base,2)&&nf_scene_packet_build(a,&original,&original_bytes);
    uint32_t identity[5]={2,state,draw[0],base,0};
    const char*fault=getenv("NF_ENTRANT_FAULT"); /* Research-only rejection probes. */
    size_t candidate_bytes=fault&&!strcmp(fault,"truncated")?bytes-1:bytes;
    if(composed)composed=nf_scene_packet_insert_wall(original,original_bytes,surface,candidate_bytes,identity,anchor,&expanded,&expanded_bytes);
    if(composed&&fault&&!strcmp(fault,"after-compose"))composed=0;
    if(composed){
     uint16_t bounds[256][4];unsigned extra=0;NFScenePacket view;
     composed=sample_bounds(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,pose,&bounds[0][0],256,&extra)&&extra==1&&nf_scene_packet_view(expanded,expanded_bytes,&view);
     if(composed){
      entrant_clips=*active_clips;
      memcpy(&entrant_clips.count,view.section[1].data+4,4);
      unsigned ordinal=0;
      for(unsigned j=0;j<=active_clips->count;j++){uint32_t index;memcpy(&index,a->section[2].data+8+j*4,4);if(index!=UINT32_MAX)memcpy(entrant_clips.bounds[index],bounds[ordinal++],8);}
      entrant_clips.kind[entrant_clips.count-1]=2;
      memcpy(entrant_clips.bounds[entrant_clips.count-1],p+6,8);
      if(prefix){
       char path[1200],stem[1100];snprintf(stem,sizeof(stem),"%s-e%llu-s%u-a%.9f",prefix,(unsigned long long)clip_epoch,a->serial,packet_presented_time.alpha);
       snprintf(path,sizeof(path),"%s.bin",stem);FILE*f=fopen(path,"wb");composed=f&&fwrite(expanded,1,expanded_bytes,f)==expanded_bytes;if(f)fclose(f);
       void*new_packet=NULL;size_t new_bytes=0;
       if(composed&&nf_scene_packet_build(b,&new_packet,&new_bytes)){
        snprintf(path,sizeof(path),"%s-new.bin",stem);f=fopen(path,"wb");composed=f&&fwrite(new_packet,1,new_bytes,f)==new_bytes;if(f)fclose(f);
       }else composed=0;
       nf_scene_packet_free(new_packet);
       snprintf(path,sizeof(path),"%s.clips",stem);f=fopen(path,"wb");
       uint32_t header[5]={0x3150434e,a->serial,a->begin_refresh,a->end_refresh,entrant_clips.count};
       composed=composed&&f&&fwrite(header,4,5,f)==5&&fwrite(&packet_presented_time.alpha,8,1,f)==1;
       if(composed)for(unsigned j=0;j<entrant_clips.count;j++)if(fwrite(view.section[4].data+8+j*20,1,20,f)!=20||fwrite(entrant_clips.bounds[j],2,4,f)!=4)composed=0;
       if(f)fclose(f);
      }
      if(composed&&getenv("NF_LIVE_ENTRANTS")&&!entrant_frame){
       entrant_frame=expanded;expanded=NULL;active_clips=&entrant_clips;
       for(unsigned j=1;j<=3;j++)preview_memory[j+1]=(PreviewMemory){view.section[j].data,view.section[j].size};
       entrant_applied++;
      }
     }
    }
    printf("entrant_packet scene=%u composed=%d bytes=%llu\n",a->serial,composed,(unsigned long long)expanded_bytes);
    nf_scene_packet_free(original);nf_scene_packet_free(expanded);
   }
   if(surface)free_candidate(surface);
   if(entrant_frame)return; /* Active packet count now includes the candidate. */
  }
 }
}
static void live_clip_pair(const NFScenePacket*a,const NFScenePacket*b){
 if(!sampled_enabled)return;
 uint32_t pa[26],pb[26],pose[26];uint16_t bounds[256][4];unsigned entrants=0;
 if(!active_clips||!read_pose(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,pa)||!read_pose(clip_epoch,b->serial,b->begin_refresh,b->end_refresh,pb)||!sample_pose(pa,pb,packet_presented_time.alpha,pose)||!sample_bounds(clip_epoch,a->serial,a->begin_refresh,a->end_refresh,pose,&bounds[0][0],256,&entrants)){sampled_unavailable++;return;}
 /* Retain the whole captured clipping set until entrant geometry is supported. */
 if(entrants){printf("sampled_entrant epoch=%llu older=%u newer=%u alpha=%.9f count=%u\n",(unsigned long long)clip_epoch,a->serial,b->serial,packet_presented_time.alpha,entrants);audit_entrants(a,b,pose);if(!entrant_frame)sampled_entrants++;return;}
 static LiveClips sampled;sampled=*active_clips;unsigned ordinal=0;
 for(unsigned i=0;i<=sampled.count;i++){
  uint32_t index;memcpy(&index,a->section[2].data+8+i*4,4);
  if(index!=UINT32_MAX)memcpy(sampled.bounds[index],bounds[ordinal++],8);
 }
 active_clips=&sampled;sampled_applied++;
}
static int capture_clips(uint64_t epoch,const void*data,size_t size){
 NFScenePacket p;if(!nf_scene_packet_view(data,size,&p))return 0;
 LiveClips item={0};item.serial=p.serial;item.begin=p.begin_refresh;item.end=p.end_refresh;
 memcpy(&item.count,p.section[1].data+4,4);if(item.count>256)return 0;
 unsigned ordinal=0;
 for(unsigned i=0;i<=item.count;i++){
  uint32_t index;memcpy(&index,p.section[2].data+8+i*4,4);if(index==UINT32_MAX)continue;
  memcpy(&item.kind[index],p.section[4].data+8+index*20,4);
  if(!read_bounds(epoch,p.serial,p.begin_refresh,p.end_refresh,ordinal++,item.bounds[index]))return 0;
 }
 if(epoch!=clip_epoch){memset(live_clips,0,sizeof(live_clips));clip_cursor=0;clip_epoch=epoch;}
 item.valid=1;live_clips[clip_cursor++%16]=item;return 1;
}
static void live_clip_select(const NFScenePacket*p){
 active_clips=NULL;if(!clip_enabled)return;
 for(unsigned i=0;i<16;i++)if(live_clips[i].valid&&live_clips[i].serial==p->serial&&live_clips[i].begin==p->begin_refresh&&live_clips[i].end==p->end_refresh){active_clips=&live_clips[i];break;}
 if(!active_clips)exit(38);
 if(read_pose){uint32_t pose[26];if(read_pose(clip_epoch,p->serial,p->begin_refresh,p->end_refresh,pose))pose_available++;else pose_expired++;}
}
static void live_clip_surface(int ring){
 if(!clip_enabled)return;
 if(ring<0){glDisable(GL_SCISSOR_TEST);return;}
 if(!active_clips||(unsigned)ring>=active_clips->count)exit(39);
 if(active_clips->kind[ring]!=2)return;
 const uint16_t*b=active_clips->bounds[ring];
 int l=b[0]>240?240:b[0],r=b[1]>240?240:b[1],t=b[2]>160?160:b[2],bottom=b[3]>160?160:b[3];
 int x0=(int)ceil(300+l*13.5-.5),x1=(int)ceil(300+r*13.5-.5),y0=(int)ceil((160-bottom)*13.5-.5),y1=(int)ceil((160-t)*13.5-.5);
 glEnable(GL_SCISSOR_TEST);glScissor(x0,y0,x1>x0?x1-x0:0,y1>y0?y1-y0:0);
}
/* Optional private replay export, only while the exact final pair is pinned. */
static int export_clip_pair(NFSnapshotStore*s,double target,const char*prefix){
 NFSnapshotPair pair;if(nf_snapshot_acquire(s,target,0,&pair)!=NF_TIME_READY)return 0;
 NFScenePacket packet,newer;int ok=0;char path[1024];FILE*f=NULL;
 if(!nf_scene_packet_view(pair.older,pair.older_size,&packet))goto done;
 live_clip_select(&packet);if(!active_clips)goto done;
 if(sampled_enabled){if(!nf_scene_packet_view(pair.newer,pair.newer_size,&newer))goto done;live_clip_pair(&packet,&newer);}
 const void*data[2]={pair.older,pair.newer};size_t sizes[2]={pair.older_size,pair.newer_size};
 for(unsigned i=0;i<2;i++){
  snprintf(path,sizeof(path),"%s-%u.bin",prefix,i);f=fopen(path,"wb");if(!f)goto done;
  int written=fwrite(data[i],1,sizes[i],f)==sizes[i];fclose(f);f=NULL;if(!written)goto done;
 }
 snprintf(path,sizeof(path),"%s.clips",prefix);f=fopen(path,"wb");if(!f)goto done;
 uint32_t header[5]={0x3150434e,packet.serial,packet.begin_refresh,packet.end_refresh,active_clips->count};
 if(fwrite(header,4,5,f)!=5||fwrite(&pair.time.alpha,8,1,f)!=1)goto done;
 for(unsigned i=0;i<active_clips->count;i++)if(fwrite(packet.section[4].data+8+i*20,1,20,f)!=20||fwrite(active_clips->bounds[i],2,4,f)!=4)goto done;
 ok=1;
done:if(f)fclose(f);nf_snapshot_release(s);return ok;
}
typedef int (*LiveSink)(void*,uint64_t,const void*,size_t);
static unsigned received,rebuilt_count,rebuild_failed;
static double rebuild_ms,compare_ms_total;static LARGE_INTEGER rebuild_frequency;
static int(*retained_extract)(uint64_t,uint32_t,uint32_t,uint32_t,void**,size_t*);
static void(*retained_free)(void*);
static int(*ordered_publish)(NFSnapshotStore*,uint64_t,const void*,size_t);
static int retain_scene(void*context,uint64_t epoch,const void*data,size_t size){
 if(ordered_publish){
  if(clip_enabled&&!capture_clips(epoch,data,size)){rebuild_failed++;return 0;}
  LARGE_INTEGER start,end;QueryPerformanceCounter(&start);
  int ok=ordered_publish(context,epoch,data,size);QueryPerformanceCounter(&end);
  rebuild_ms+=(end.QuadPart-start.QuadPart)*1000.0/rebuild_frequency.QuadPart;
  if(ok){received++;rebuilt_count++;}else rebuild_failed++;
  return ok;
 }
 void*owned=NULL;size_t owned_size=0;
 if(retained_extract){
  NFScenePacket packet;
  if(!nf_scene_packet_view(data,size,&packet)){rebuild_failed++;return 0;}
  LARGE_INTEGER start,end;QueryPerformanceCounter(&start);
  int extracted=retained_extract(epoch,packet.serial,packet.begin_refresh,packet.end_refresh,&owned,&owned_size);QueryPerformanceCounter(&end);
  rebuild_ms+=(end.QuadPart-start.QuadPart)*1000.0/rebuild_frequency.QuadPart;
  if(!extracted){rebuild_failed++;return 0;}
  start=end;int identical=owned_size==size&&!memcmp(owned,data,size);QueryPerformanceCounter(&end);
  compare_ms_total+=(end.QuadPart-start.QuadPart)*1000.0/rebuild_frequency.QuadPart;
  if(!identical){retained_free(owned);rebuild_failed++;return 0;}
  data=owned;size=owned_size;rebuilt_count++;
 }
 int ok=nf_scene_packet_push(context,epoch,data,size);if(owned)retained_free(owned);if(ok)received++;return ok;
}
#ifndef NF_LIVE_PREVIEW_NO_MAIN
int main(int argc,char**argv){
 QueryPerformanceFrequency(&rebuild_frequency);
 int reload=0,retained=0,ordered=0;
 if(argc<6||argc>8)return 1;
 for(int i=6;i<argc;i++){if(!strcmp(argv[i],"--reload"))reload=1;else if(!strcmp(argv[i],"--retained"))retained=1;else if(!strcmp(argv[i],"--ordered")){ordered=1;retained=1;}else if(!strcmp(argv[i],"--ordered-clips")){ordered=retained=clip_enabled=1;}else if(!strcmp(argv[i],"--sampled-clips")){ordered=retained=clip_enabled=sampled_enabled=1;}else return 1;} /* DLL, ROM, saved state, CSV, final image prefix */
 HMODULE bridge=LoadLibraryA(argv[1]);if(!bridge)return 2;
 unsigned(*queue_capacity)(void)=(void*)GetProcAddress(bridge,"nfs_visibility_queue_capacity");
 if(sampled_enabled&&(!queue_capacity||queue_capacity()!=NF_VISIBILITY_QUEUE_CAPACITY)){fprintf(stderr,"visibility capacity mismatch\n");FreeLibrary(bridge);return 11;}
 int(*init)(const char*,const char*)=(void*)GetProcAddress(bridge,"nf_init");
 int(*state)(const char*,int)=(void*)GetProcAddress(bridge,"nf_state");
 int(*sink)(LiveSink,void*)=(void*)GetProcAddress(bridge,"nf_native_scene_sink");
 void(*frame)(unsigned)=(void*)GetProcAddress(bridge,"nf_frame");
 void(*close_game)(void)=(void*)GetProcAddress(bridge,"nf_close");
 uint64_t(*epoch)(void)=(void*)GetProcAddress(bridge,"nf_native_scene_epoch");
 uint32_t(*refresh)(void)=(void*)GetProcAddress(bridge,"nf_native_scene_refresh");
 if(!init||!state||!sink||!frame||!close_game||!epoch||!refresh)return 3;
 NFSnapshotStore*s=nf_snapshot_create(32*1024*1024);if(!s)return 4;
 if(!init(argv[2],"")||!state(argv[3],0)||!sink(retain_scene,s))return 5;
 if(retained){
  if(ordered){ordered_publish=(void*)GetProcAddress(bridge,"nf_live_completed_publish_ordered");if(!ordered_publish)return 10;}
  if(clip_enabled){read_bounds=(void*)GetProcAddress(bridge,"nf_live_completed_surface_bounds");read_pose=(void*)GetProcAddress(bridge,"nf_live_completed_visibility_pose");if(!read_bounds||!read_pose)return 10;}
  if(sampled_enabled){sample_pose=(void*)GetProcAddress(bridge,"nf_visibility_pose_sample");sample_bounds=(void*)GetProcAddress(bridge,"nf_live_completed_sampled_bounds");if(!sample_pose||!sample_bounds)return 10;}
  if(sampled_enabled){sample_queue=(void*)GetProcAddress(bridge,"nf_live_completed_queue_plans");extract_candidate=(void*)GetProcAddress(bridge,"nf_live_completed_wall_candidate");free_candidate=(void*)GetProcAddress(bridge,"nf_surface_free");read_dispatch=(void*)GetProcAddress(bridge,"nf_live_completed_dispatch");if(!sample_queue||!extract_candidate||!free_candidate||!read_dispatch)return 10;}
  if(sampled_enabled){read_snapshot=(void*)GetProcAddress(bridge,"nf_live_completed_snapshot_read");if(!read_snapshot)return 10;}
  if(sampled_enabled){read_regions=(void*)GetProcAddress(bridge,"nf_live_completed_region_invocations");read_origin=(void*)GetProcAddress(bridge,"nf_live_completed_surface_origin");read_wall_pass=(void*)GetProcAddress(bridge,"nf_live_completed_wall_pass");if(!read_regions||!read_origin||!read_wall_pass)return 10;}
  retained_extract=(void*)GetProcAddress(bridge,"nf_live_completed_scene_extract");retained_free=(void*)GetProcAddress(bridge,"nf_scene_packet_free");
  int(*enable)(const void*,size_t,size_t)=(void*)GetProcAddress(bridge,"nf_live_visibility_enable");void(*audit)(int)=(void*)GetProcAddress(bridge,"nf_live_surface_audit_enable");
  if(!retained_extract||!retained_free||!enable||!audit)return 10;
  FILE*rom=fopen(argv[2],"rb");if(!rom)return 11;fseek(rom,0,SEEK_END);long bytes=ftell(rom);rewind(rom);
  if(bytes<=0||bytes>32*1024*1024){fclose(rom);return 11;}
  void*copy=malloc((size_t)bytes);if(!copy){fclose(rom);return 11;}
  int ok=fread(copy,1,(size_t)bytes,rom)==(size_t)bytes&&enable(copy,(size_t)bytes,16*1024*1024);free(copy);fclose(rom);if(!ok)return 12;audit(1);
 }
 FILE*log=fopen(argv[4],"wb");if(!log)return 6;
 fprintf(log,"refresh,epoch,rendered,target,older,newer,alpha,simulation_capture_ms,render_ms,total_ms,rebuild_ms,reference_compare_ms\n");
 preview_keep_context=1;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);unsigned rendered=0;int result=0;
 char*args[]={argv[0],"unused","unused",argv[5]};double final_target=0;
 unsigned stale_suppressed=0;
 for(unsigned i=0;i<(reload?360u:180u);i++){
  if(i==180){
   uint64_t previous=epoch();if(!state(argv[3],0)||epoch()<=previous){result=7;break;}
   NFSnapshotPair old;
   if(nf_snapshot_acquire(s,final_target,0,&old)!=NF_TIME_READY){nf_snapshot_release(s);result=8;break;}
   int stale=old.time.epoch!=epoch();nf_snapshot_release(s);
   if(!stale){result=9;break;}stale_suppressed++;
  }
  double before_rebuild=rebuild_ms,before_compare=compare_ms_total;
  LARGE_INTEGER start,sim,end;QueryPerformanceCounter(&start);frame(1);QueryPerformanceCounter(&sim);
  uint32_t now=refresh();uint64_t current_epoch=epoch();double target=(double)now-5;NFSnapshotPair pair;
  int ready=nf_snapshot_acquire(s,target,0,&pair)==NF_TIME_READY;
  if(ready)ready=pair.time.epoch==current_epoch;
  nf_snapshot_release(s);
  if(ready){result=render_packet_at(s,target,args);if(result)break;rendered++;final_target=target;}
  QueryPerformanceCounter(&end);
  fprintf(log,"%u,%llu,%d,%.0f,%llu,%llu,%.9f,%.6f,%.6f,%.6f,%.6f,%.6f\n",now,(unsigned long long)current_epoch,ready,target,
   ready?(unsigned long long)packet_presented_time.older:0,ready?(unsigned long long)packet_presented_time.newer:0,ready?packet_presented_time.alpha:0,
   (sim.QuadPart-start.QuadPart)*1000.0/frequency.QuadPart,(end.QuadPart-sim.QuadPart)*1000.0/frequency.QuadPart,(end.QuadPart-start.QuadPart)*1000.0/frequency.QuadPart,rebuild_ms-before_rebuild,compare_ms_total-before_compare);
 }
 fclose(log);
 if(rebuild_failed&&!result)result=27;
 printf("retained_rebuilt=%u retained_failed=%u\n",rebuilt_count,rebuild_failed);
 printf("result=%d live_packets=%u rendered=%u contexts=%u uploads=%u hits=%u lighting_fallbacks=%u final_target=%.0f stale_suppressed=%u\n",result,received,rendered,preview_contexts,preview_uploads,preview_hits,lighting_fallback,final_target,stale_suppressed);
 if(!result&&rendered){preview_measure_only=0;result=render_packet_at(s,final_target,args);}
 const char*export_prefix=getenv("NF_LIVE_CLIP_EXPORT");
 if(!result&&rendered&&clip_enabled&&export_prefix&&!export_clip_pair(s,final_target,export_prefix))result=40;
 if(clip_enabled)printf("render_pose_available=%u render_pose_expired=%u\n",pose_available,pose_expired);
 if(sampled_enabled)printf("sampled_clips_applied=%u unavailable=%u entrant_fallback=%u\n",sampled_applied,sampled_unavailable,sampled_entrants);
 printf("entrant_live_applied=%u released=%u\n",entrant_applied,entrant_released);
 live_frame_release();preview_shutdown();close_game();nf_snapshot_release(s);nf_snapshot_destroy(s);FreeLibrary(bridge);return result;
}
#endif
