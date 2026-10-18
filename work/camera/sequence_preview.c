#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 int verify=argc==4&&!strcmp(argv[3],"--verify-last");if(argc!=3&&!verify)return 1;
 char paths[256][1024];uint32_t times[256];unsigned count=0;FILE*manifest=fopen(argv[1],"rb");if(!manifest)return 2;
 while(count<256&&fgets(paths[count],sizeof(paths[count]),manifest)){
  paths[count][strcspn(paths[count],"\r\n")]=0;FILE*f=fopen(paths[count],"rb");uint32_t header[8];
  if(!f||fread(header,4,8,f)!=8)return 3;
  fclose(f);
  if(header[0]!=0x3150534e||(count&&header[6]<=times[count-1]))return 3;
  times[count++]=header[6];
 }int extra=fgetc(manifest);fclose(manifest);if(count<2||extra!=EOF||times[count-1]-times[0]>36000||times[count-1]==UINT32_MAX)return 3;
 NFSnapshotStore*s=nf_snapshot_create(128*1024*1024);if(!s)return 4;
 FILE*log=fopen(argv[2],"wb");if(!log)return 5;fprintf(log,"refresh,target,older,newer,alpha,render_ms\n");
 preview_keep_context=1;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 unsigned next=0,frames=0;int result=0;double maximum=0,total=0;LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);
 char*render_args[]={argv[0],"unused","unused","sequence-output"};
 for(uint32_t now=times[0];now<=times[count-1];now++){
  while(next<count&&times[next]<=now){NFScenePacket packet;if(!enqueue_file(s,paths[next],&packet)){result=6;break;}next++;}if(result)break;
  if(now-times[0]<5)continue;
  LARGE_INTEGER begin,finish;QueryPerformanceCounter(&begin);result=render_packet_at(s,now-5,render_args);QueryPerformanceCounter(&finish);if(result)break;
  double ms=(finish.QuadPart-begin.QuadPart)*1000.0/frequency.QuadPart;total+=ms;if(ms>maximum)maximum=ms;frames++;
  fprintf(log,"%u,%.0f,%llu,%llu,%.9f,%.6f\n",now,packet_presented_time.target,(unsigned long long)packet_presented_time.older,(unsigned long long)packet_presented_time.newer,packet_presented_time.alpha,ms);
 }
 fclose(log);printf("result=%d source_scenes=%u display_samples=%u contexts=%u uploads=%u hits=%u lighting_fallbacks=%u mean_ms=%.6f max_ms=%.6f\n",result,next,frames,preview_contexts,preview_uploads,preview_hits,lighting_fallback,frames?total/frames:0,maximum);
 if(verify&&!result){
  char path[1200];snprintf(path,sizeof(path),"%s.cached.ppm",argv[2]);FILE*f=fopen(path,"wb");uint8_t*pixels=malloc(3840*2160*3);
  if(!f||!pixels)return 7;
  glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,pixels);fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)fwrite(pixels+y*3840*3,3,3840,f);fclose(f);free(pixels);
  preview_shutdown();preview_measure_only=0;snprintf(path,sizeof(path),"%s.reference",argv[2]);render_args[3]=path;
  result=render_packet_at(s,times[count-1]-5,render_args);printf("fresh_reference_result=%d\n",result);
 }
 preview_shutdown();nf_snapshot_release(s);nf_snapshot_destroy(s);return result;
}
