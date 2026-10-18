#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
#include "indexed_copy_gpu.h"
int main(int argc,char**argv){
 if(argc!=2)return 1;FILE*f=fopen(argv[1],"rb");if(!f)return 2;
 uint8_t asset[38440];size_t bytes=fread(asset,1,sizeof(asset),f);int extra=fgetc(f);fclose(f);if(bytes<40||extra!=EOF)return 3;
 uint32_t kind,page,offset;const uint8_t*indices;size_t count;if(!nf_indexed_operation_view(asset,bytes,&kind,&page,&offset,&indices,&count))return 4;
 if(preview_context_open())return 5;preview_generation++;preview_zero_valid=preview_display_palette_valid=1;
 for(unsigned y=0;y<160;y++)for(unsigned i=0;i<256;i++)preview_display_palette[y][i]=(i*131+y*997)&32767;
 glViewport(0,0,3840,2160);glClearColor(1,0,1,1);glClear(GL_COLOR_BUFFER_BIT);glDisable(GL_DITHER);
 if(!indexed_copy_gpu_draw(asset,bytes))return 6;
 uint8_t*out=malloc(3840u*2160u*3);if(!out)return 7;glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,out);if(glGetError()!=GL_NO_ERROR)return 8;
 unsigned changed=0;
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){
  unsigned expected[3]={255,0,255};if(x>=300&&x<3540){unsigned sx=(unsigned)floor((x-300+.5)/13.5),sy=(unsigned)floor((2160-y-.5)/13.5),at=sy*240+sx;
   if(at>=offset&&at<offset+count){unsigned color=preview_display_palette[sy][indices[at-offset]];for(unsigned k=0;k<3;k++)expected[k]=((color>>(k*5))&31)*255/31;changed++;}}
  for(unsigned k=0;k<3;k++)if(out[(y*3840+x)*3+k]!=expected[k]){printf("mismatch %u %u\n",x,y);return 9;}
 }
 free(out);preview_shutdown();printf("PASS indexed_operation_4k kind=%u bytes=%zu pixels=8294400 written=%u outside_exact=1\n",kind,count,changed);return 0;
}
