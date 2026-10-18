#include <stdio.h>
#include <windows.h>
#include "hud_row_pool.h"
static double now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart*1000/f.QuadPart;}
int main(int argc,char**argv){
 if(argc!=2)return 2;
 size_t bytes=160*sizeof(NFHudLayerRow);unsigned char*data=malloc(bytes),*out=malloc(bytes);FILE*f=fopen(argv[1],"rb");
 if(!data||!out||!f||fread(data,1,bytes,f)!=bytes)return 3;
 if(fgetc(f)!=EOF)return 3;
 fclose(f);
 double create[2]={0},validate[2]={0},copy[2]={0};size_t stored[2]={0};volatile unsigned sink=0;
 /* Rotate order each round so no mode always receives the same cache position. */
 for(unsigned round=0;round<36;round++)for(unsigned pos=0;pos<2;pos++){
  unsigned mode=(round+pos)%2;
  _putenv("NF_TEST_HUD_POOL_PLANES=1");_putenv("NF_TEST_HUD_POOL_SAMPLE_FILTER=");
  if(mode==1)_putenv("NF_TEST_HUD_POOL_SAMPLE_FILTER=1");
  
  double t=now();memcpy(out,data,bytes);sink+=out[round%bytes];copy[mode]+=now()-t;
  t=now();NFHudRowPool*p=nf_hud_pool_create(data,bytes,7);create[mode]+=now()-t;if(!p)return 4;
  stored[mode]=p->bytes;t=now();int valid=nf_hud_pool_valid(p,p->bytes,7);validate[mode]+=now()-t;if(!valid)return 5;
  if(!nf_hud_pool_expand(p,p->bytes,7,out,bytes)||memcmp(out,data,bytes))return 6;
  free(p);
 }
 for(unsigned m=0;m<2;m++)printf("mode=%u iterations=36 full_bytes=%zu stored_bytes=%zu copy_ms=%.6f create_ms=%.6f validate_ms=%.6f exact=1 sink=%u\n",m,bytes,stored[m],copy[m]/36,create[m]/36,validate[m]/36,sink);
 free(data);free(out);return 0;
}

