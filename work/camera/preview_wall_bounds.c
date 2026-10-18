/* Frozen screen bounds are ONLY for an exact-pose diagnostic. Never enable
   this path for interpolated camera motion; recover world visibility first. */
static void diagnostic_clip(int);
#define NF_DIAGNOSTIC_SURFACE_CLIP diagnostic_clip
#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
static double bounds[128][2];
static void diagnostic_clip(int surface){
 if(surface<0){glDisable(GL_CLIP_PLANE0);glDisable(GL_CLIP_PLANE1);return;}
 double left[4]={1,0,0,-bounds[surface][0]},right[4]={-1,0,0,bounds[surface][1]};
 glClipPlane(GL_CLIP_PLANE0,left);glClipPlane(GL_CLIP_PLANE1,right);glEnable(GL_CLIP_PLANE0);glEnable(GL_CLIP_PLANE1);
}
int main(int argc,char**argv){
 if(argc!=5)return 1;
 NFSnapshotStore*s=nf_snapshot_create(32*1024*1024);NFScenePacket a,b;
 if(!s||!enqueue_file(s,argv[1],&a)||!enqueue_file(s,argv[2],&b))return 2;
 FILE*f=fopen(argv[3],"rb");if(!f)return 3;
 for(unsigned i=0;i<128;i++){bounds[i][0]=0;bounds[i][1]=240;}
 uint32_t count;if(fread(&count,4,1,f)!=1||count>128||fread(bounds,16,count,f)!=count)return 4;fclose(f);
 preview_keep_context=1;_putenv("NF_PREVIEW_PHASE=0");char*args[]={argv[0],"unused","unused",argv[4]};
 int result=render_packet_at(s,a.end_refresh,args);preview_shutdown();nf_snapshot_destroy(s);return result;
}
