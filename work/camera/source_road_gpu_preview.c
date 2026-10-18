#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=3)return 1;
 NFSnapshotStore*s=nf_snapshot_create(128*1024*1024);NFScenePacket a;
 if(!s||!enqueue_file(s,argv[1],&a)){nf_snapshot_destroy(s);return 22;}
 for(unsigned y=0;y<160;y++)preview_zero_colors[y]=(uint16_t)((y*137)&32767);
 preview_zero_valid=1;preview_zero_background=1;preview_keep_context=1;preview_measure_only=0;
 _putenv("NF_SOURCE_ROAD_ENDPOINT=1");char*args[]={argv[0],argv[1],argv[1],argv[2]};
 int result=render_packet_at(s,a.end_refresh,args);
 printf("source_road_rings=%llu result=%d\n",(unsigned long long)preview_source_road_rings,result);
 preview_shutdown();nf_snapshot_destroy(s);return result;
}
