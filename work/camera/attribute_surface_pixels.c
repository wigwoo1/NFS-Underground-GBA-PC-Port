/* Diagnostic-only surface suppression; normal builds have no suppression. */
static int skipped_surface=-1;
#define NF_DIAGNOSTIC_SKIP_SURFACE skipped_surface
#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=3)return 1;
 NFSnapshotStore*s=nf_snapshot_create(32*1024*1024);NFScenePacket a,b,v;NFSnapshotPair pair;
 if(!s||!enqueue_file(s,argv[1],&a)||!enqueue_file(s,argv[2],&b))return 2;
 if(nf_snapshot_acquire(s,a.end_refresh,0,&pair)!=NF_TIME_READY||!nf_scene_packet_view(pair.older,pair.older_size,&v))return 3;
 uint32_t ids[129][5],count;memcpy(&count,v.section[4].data+4,4);if(count>129)return 4;
 memcpy(ids,v.section[4].data+8,count*20);nf_snapshot_release(s);
 preview_keep_context=1;preview_measure_only=1;_putenv("NF_PREVIEW_PHASE=0");
 char*args[]={argv[0],"unused","unused","unused"};
 if(render_packet_at(s,a.end_refresh,args))return 5;
 /* Original view coordinates x=50..140, y=30..90, scaled 13.5x. */
 enum{W=1215,H=810,BYTES=W*H*3};uint8_t*base=malloc(BYTES),*pixels=malloc(BYTES);if(!base||!pixels)return 6;
 glReadPixels(975,945,W,H,GL_RGB,GL_UNSIGNED_BYTE,base);
 FILE*f=fopen("work/camera/surface-attribution.csv","wb");if(!f)return 7;
 fprintf(f,"surface,kind,state,source,material,changed_roi_pixels\n");
 for(unsigned i=0;i+1<count;i++){
  skipped_surface=(int)i;if(render_packet_at(s,a.end_refresh,args))return 8;
  glReadPixels(975,945,W,H,GL_RGB,GL_UNSIGNED_BYTE,pixels);
  unsigned changed=0;for(unsigned p=0;p<W*H;p++)changed+=memcmp(base+p*3,pixels+p*3,3)!=0;
  fprintf(f,"%u,%u,%08x,%08x,%08x,%u\n",i,ids[i][0],ids[i][1],ids[i][2],ids[i][3],changed);
 }
 skipped_surface=-1;if(render_packet_at(s,a.end_refresh,args))return 9;
 glReadPixels(975,945,W,H,GL_RGB,GL_UNSIGNED_BYTE,pixels);
 int restored=!memcmp(base,pixels,BYTES);fclose(f);free(base);free(pixels);
 printf("surfaces_audited=%u restored_roi_byte_identical=%d\n",count-1,restored);
 preview_shutdown();nf_snapshot_destroy(s);return restored?0:10;
}
