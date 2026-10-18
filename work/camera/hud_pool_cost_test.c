#include <stdio.h>
#include <windows.h>
#include "hud_row_pool.h"
static double now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart*1000/f.QuadPart;}
int main(int argc,char**argv){if(argc<2||argc>3)return 2;if(argc==3)_putenv("NF_TEST_HUD_POOL_PREVIOUS_HINT=1");size_t bytes=160*sizeof(NFHudLayerRow);uint8_t*data=malloc(bytes),*out=malloc(bytes);FILE*f=fopen(argv[1],"rb");if(!f||fread(data,1,bytes,f)!=bytes)return 3;fclose(f);double create=0,validate=0,copy=0;unsigned iterations=80;size_t pool_bytes=0;volatile unsigned sink=0;
 for(unsigned i=0;i<iterations;i++){double t=now();memcpy(out,data,bytes);sink+=out[(i*34944)%bytes];copy+=now()-t;t=now();NFHudRowPool*p=nf_hud_pool_create(data,bytes,7);create+=now()-t;if(!p)return 4;pool_bytes=p->bytes;t=now();if(!nf_hud_pool_valid(p,p->bytes,7))return 5;validate+=now()-t;if(!nf_hud_pool_expand(p,p->bytes,7,out,bytes)||memcmp(data,out,bytes))return 6;free(p);}
 printf("iterations=%u full_bytes=%zu pool_bytes=%zu full_copy_ms=%.6f pool_create_ms=%.6f pool_validate_ms=%.6f sink=%u\n",iterations,bytes,pool_bytes,copy/iterations,create/iterations,validate/iterations,sink);free(data);free(out);return 0;}
