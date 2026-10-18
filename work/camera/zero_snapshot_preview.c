/* Explicit row-color diagnostic; live callers must bind exact refresh owner. */
#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
int main(int argc,char**argv){
 if(argc!=4)return 1;
 FILE*f=fopen(argv[3],"rb");if(!f)return 38;
 int ok=fread(preview_zero_colors,2,160,f)==160&&fgetc(f)==EOF;fclose(f);if(!ok)return 38;
 NFSnapshotStore*s=nf_snapshot_create(128*1024*1024);NFScenePacket packet;
 if(!s||!enqueue_file(s,argv[1],&packet)){nf_snapshot_destroy(s);return 22;}
 preview_keep_context=1;preview_zero_valid=1;preview_zero_background=1;_putenv("NF_PREVIEW_PHASE=0");
 char*args[]={argv[0],argv[1],argv[1],argv[2]};int result=render_packet_at(s,packet.end_refresh,args);
 if(!result){unsigned char*rgba=malloc(3840u*2160u*4);if(!rgba)result=39;else{glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,rgba);char path[1024];snprintf(path,sizeof(path),"%s.rgba",argv[2]);FILE*out=fopen(path,"wb");if(!out)result=39;else{if(fwrite(rgba,4,3840u*2160u,out)!=3840u*2160u)result=39;fclose(out);}free(rgba);}}
 preview_zero_valid=0;preview_shutdown();nf_snapshot_release(s);nf_snapshot_destroy(s);return result;
}
