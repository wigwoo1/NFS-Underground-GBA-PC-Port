/* Frozen owned-scene diagnostic: one real snapshot, no invented future state. */
#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=3)return 1;
 NFSnapshotStore*s=nf_snapshot_create(128*1024*1024);NFScenePacket packet;
 if(!s||!enqueue_file(s,argv[1],&packet)){nf_snapshot_destroy(s);return 22;}
 preview_keep_context=1;_putenv("NF_PREVIEW_PHASE=0");
 char*args[]={argv[0],argv[1],argv[1],argv[2]};
 int result=render_packet_at(s,packet.end_refresh,args);
 preview_shutdown();nf_snapshot_release(s);nf_snapshot_destroy(s);return result;
}
