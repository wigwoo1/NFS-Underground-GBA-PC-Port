#include "nfsug_capture.h"
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"capture check failed at line %d\n",__LINE__);return 1;}}while(0)
static FILE*output(const char*directory,const char*name){char path[1024];if(snprintf(path,sizeof(path),"%s/%s",directory,name)>=(int)sizeof(path))return NULL;return fopen(path,"wb");}
static int dump_frame(NFAAndroidCore*c,FILE*f){const uint32_t*p=nfa_core_pixels(c);return p&&fwrite(p,1,153600,f)==153600;}
int main(int argc,char**argv){
 CHECK(argc==5);int enabled=atoi(argv[4]);CHECK(enabled==0||enabled==1);
 FILE*f=fopen(argv[2],"rb");CHECK(f);fseek(f,0,SEEK_END);long bytes=ftell(f);rewind(f);CHECK(bytes>0&&bytes<=1024*1024);
 void*state=malloc((size_t)bytes);CHECK(state&&fread(state,1,(size_t)bytes,f)==(size_t)bytes);fclose(f);
 NFAAndroidCore*c=nfa_core_open(argv[1]);CHECK(c);CHECK(nfa_core_load_state(c,state,(size_t)bytes));
 if(enabled)CHECK(nfa_core_capture_enable(c,1));
 FILE*frames=output(argv[3],"frames.raw"),*audio=output(argv[3],"audio.raw"),*packets=output(argv[3],"packets.bin");CHECK(frames&&audio&&packets);
 uint64_t initial[4],now[4],stats[8],last=0;CHECK(nfa_core_timing(c,initial));
 int16_t pcm[8192];uint64_t pcm_frames=0;
 for(unsigned i=0;i<600;i++){
  unsigned keys=1|(i>=60&&i<120?16:i>=480&&i<540?32:0);CHECK(nfa_core_step(c,keys)==1);
  CHECK(nfa_core_timing(c,now)&&now[0]==16777216&&now[1]==280896&&now[2]==initial[2]+i+1&&now[3]==i+1);
  CHECK(dump_frame(c,frames));size_t n=nfa_core_read_audio(c,pcm,4096);CHECK(n<=4096&&fwrite(pcm,4,n,audio)==n);pcm_frames+=n;
  CHECK(nfa_core_capture_stats(c,stats)&&stats[4]==0&&stats[5]==0);
  if(stats[3]!=last){
   CHECK(stats[3]==last+1);size_t size=nfa_core_capture_copy(c,NULL,0);CHECK(size>92&&size<=32*1024*1024);
   void*packet=malloc(size);CHECK(packet&&nfa_core_capture_copy(c,packet,size)==size);
   uint64_t row[3]={i+1,size,stats[1]};CHECK(fwrite(row,sizeof(row),1,packets)==1&&fwrite(packet,1,size,packets)==size);
   free(packet);last=stats[3];
  }
 }
 CHECK(!fclose(frames)&&!fclose(audio)&&!fclose(packets));
 uint64_t saved_stats[8];CHECK(nfa_core_capture_stats(c,saved_stats));CHECK(nfa_core_pause(c,1));
 for(unsigned i=0;i<10;i++){CHECK(nfa_core_step(c,1)==2);CHECK(nfa_core_timing(c,now)&&now[3]==600);CHECK(nfa_core_capture_stats(c,stats)&&!memcmp(stats,saved_stats,sizeof(stats)));}
 CHECK(nfa_core_pause(c,0));uint64_t epoch=saved_stats[1];CHECK(nfa_core_load_state(c,state,(size_t)bytes));
 CHECK(nfa_core_capture_stats(c,stats));if(enabled)CHECK(stats[1]>epoch&&!nfa_core_capture_copy(c,NULL,0));
 if(enabled){
  frames=output(argv[3],"after_load.raw");CHECK(frames);
  for(unsigned i=0;i<16;i++)CHECK(nfa_core_step(c,1)==1&&dump_frame(c,frames));
  CHECK(!fclose(frames)&&nfa_core_capture_stats(c,stats)&&stats[3]>saved_stats[3]);
  size_t count=nfa_core_capture_copy(c,NULL,0);void*latest=malloc(count);CHECK(count>92&&latest&&nfa_core_capture_copy(c,latest,count)==count);
  f=output(argv[3],"after_load_packet.bin");CHECK(f&&fwrite(latest,1,count,f)==count&&!fclose(f));free(latest);
  CHECK(nfa_core_load_state(c,state,(size_t)bytes));
 }
 CHECK(nfa_core_capture_enable(c,0));frames=output(argv[3],"after_detach.raw");CHECK(frames);
 for(unsigned i=0;i<16;i++){CHECK(nfa_core_step(c,1)==1&&dump_frame(c,frames));}CHECK(!fclose(frames));
 CHECK(nfa_core_capture_enable(c,1));nfa_core_close(c);
 c=nfa_core_open(argv[1]);CHECK(c&&nfa_core_load_state(c,state,(size_t)bytes)&&nfa_core_capture_enable(c,1));
 frames=output(argv[3],"after_reopen.raw");CHECK(frames);for(unsigned i=0;i<16;i++)CHECK(nfa_core_step(c,1)==1&&dump_frame(c,frames));
 CHECK(!fclose(frames));nfa_core_close(c);free(state);
 printf("{\"result\":\"PASS_ANDROID_CAPTURE_DIAGNOSTIC\",\"capture_enabled\":%s,\"frames\":600,\"packets\":%llu,\"pcm_frames\":%llu,\"pause_state_detach_reopen\":true,\"gpu_rendering\":false}\n",enabled?"true":"false",(unsigned long long)last,(unsigned long long)pcm_frames);
 return 0;
}
