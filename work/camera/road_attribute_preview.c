#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=4)return 1;NFSnapshotStore*s=nf_snapshot_create(128*1024*1024);NFScenePacket a,b;
 if(!s||!enqueue_file(s,argv[1],&a)||!enqueue_file(s,argv[2],&b)){nf_snapshot_destroy(s);return 22;}
 for(unsigned y=0;y<160;y++)preview_zero_colors[y]=(uint16_t)((y*137)&32767);
 preview_zero_valid=1;preview_zero_background=1;preview_keep_context=1;preview_measure_only=0;_putenv("NF_PREVIEW_PHASE=2");
 char*args[]={argv[0],argv[1],argv[2],argv[3]};int result=render_packet_at(s,(a.end_refresh+b.end_refresh)/2.,args);
 for(unsigned i=0;i<128;i++)if(preview_wall_states[i]||preview_wall_planes[i]||preview_world_indices[i]||preview_world_affine[i])result=99;
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
 for(unsigned i=0;i<128;i++)if(preview_road_attributes_present[i])result=99;
#endif
 preview_shutdown();nf_snapshot_destroy(s);return result;
}
