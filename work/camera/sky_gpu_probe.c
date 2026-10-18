/* Renderer-owned offscreen pixel test; no game core or desktop readback. */
#define NF_PACKET_NO_MAIN
#define NF_PACKET_NO_FILES
#include "packet_preview.c"
#include "live_hud_adapter.h"
#include "live_sky_adapter.h"
static int read_exact(const char*folder,const char*name,void*out,size_t size){
 char path[2048];snprintf(path,sizeof(path),"%s/%s",folder,name);FILE*f=fopen(path,"rb");if(!f)return 0;
 int ok=fread(out,1,size,f)==size&&fgetc(f)==EOF;fclose(f);return ok;
}
int main(int argc,char**argv){
 if(argc!=3&&argc!=4)return 1;
 int epoch_test=argc==4&&!strcmp(argv[3],"--stale-epoch");
 uint8_t old_data[15192],new_data[15192],asset[15376],palettes[160*512];
 if(!read_exact(argv[1],"old.nfsk",old_data,sizeof(old_data))||!read_exact(argv[1],"new.nfsk",new_data,sizeof(new_data))||
    !read_exact(argv[1],"asset.bin",asset,sizeof(asset))||!read_exact(argv[1],"palettes.bin",palettes,sizeof(palettes)))return 2;
 NFSkyBoundary old,new;if(!nf_sky_boundary_decode(old_data,sizeof(old_data),&old)||!nf_sky_boundary_decode(new_data,sizeof(new_data),&new))return 3;
 uint8_t identity[32];if(!read_exact(argv[1],"pair.bin",identity,sizeof(identity)))return 3;
 uint64_t epoch;uint32_t id[6];memcpy(&epoch,identity,8);memcpy(id,identity+8,24);
 NFScenePacket a={0},b={0};a.serial=id[0];a.begin_refresh=id[1];a.end_refresh=id[2];b.serial=id[3];b.begin_refresh=id[4];b.end_refresh=id[5];
 unsigned slots[2]={a.serial%16,b.serial%16};const NFScenePacket*packets[2]={&a,&b};const uint8_t*inputs[2]={old_data,new_data};
 for(unsigned i=0;i<2;i++){
  unsigned slot=slots[i];memcpy(live_sky_boundaries[slot].data,inputs[i],15192);memcpy(live_sky_boundaries[slot].asset,asset,15376);
  live_sky_boundaries[slot].epoch=epoch;live_sky_boundaries[slot].serial=packets[i]->serial;
  live_sky_boundaries[slot].begin=packets[i]->begin_refresh;live_sky_boundaries[slot].end=packets[i]->end_refresh;live_sky_boundaries[slot].asset_usable=1;
 }
 for(unsigned y=0;y<160;y++)memcpy(live_hud_rows[y].palette,palettes+y*512,512);
 for(unsigned i=0;i<38400;i++){live_sky_rgba[i*4]=12;live_sky_rgba[i*4+1]=34;live_sky_rgba[i*4+2]=56;live_sky_rgba[i*4+3]=255;}
 preview_keep_context=1;if(preview_context_open())return 4;
 live_sky_enabled=live_sky_continuous=live_sky_continuous_ready=1;live_sky_refresh=1;
 uint8_t*pixels=malloc(3240u*2160u*3u);if(!pixels)return 5;
 int result=0;
 for(unsigned phase=1;phase<=7;phase++){
  double alpha=phase/8.0;NFTimelineSample time={epoch,a.serial,b.serial,alpha,a.end_refresh+(b.end_refresh-a.end_refresh)*alpha};
  if(epoch_test){time.epoch++;if(live_sky_prepare_pair(&a,&b,&time))result=10;break;}
  if(!live_sky_prepare_pair(&a,&b,&time)){result=6;break;}
  if(!live_sky_draw_background()){result=7;break;}
  glReadBuffer(0x8ce0);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(300,0,3240,2160,GL_RGB,GL_UNSIGNED_BYTE,pixels);
  if(glGetError()!=GL_NO_ERROR){result=8;break;}
  char path[2048];snprintf(path,sizeof(path),"%s/phase-%u.rgb",argv[2],phase);FILE*f=fopen(path,"wb");if(!f){result=9;break;}
  for(unsigned y=0;y<160;y++)for(unsigned x=0;x<240;x++){
   unsigned px=(unsigned)floor((x+.5)*13.5),py=2159-(unsigned)floor((y+.5)*13.5);
   fwrite(pixels+((size_t)py*3240+px)*3,1,3,f);
  }
  fclose(f);
 }
 free(pixels);live_sky_close();preview_shutdown();printf("sky_gpu_pixel_result=%d stale_epoch=%d fallback_frames=%u\n",result,epoch_test,live_sky_continuous_fallbacks);return result;
}
