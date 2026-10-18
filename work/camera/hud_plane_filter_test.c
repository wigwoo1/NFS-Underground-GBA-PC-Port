#include <stdio.h>
#include "hud_row_pool.h"
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed line %u\n",__LINE__);return 1;}}while(0)
static int parity(void*d,size_t n){
 _putenv("NF_TEST_HUD_POOL_SAMPLE_FILTER=");NFHudRowPool*a=nf_hud_pool_create(d,n,9);
 _putenv("NF_TEST_HUD_POOL_SAMPLE_FILTER=1");NFHudRowPool*b=nf_hud_pool_create(d,n,9);
 int ok=a&&b&&a->bytes==b->bytes&&!memcmp(a,b,a->bytes)&&nf_hud_pool_valid(b,b->bytes,9);
 if(ok)for(unsigned row=0;row<160;row++){const uint8_t*p=nf_hud_pool_palette(b,b->bytes,9,row);if(!p||memcmp(p,(const uint8_t*)d+row*sizeof(NFHudLayerRow)+offsetof(NFHudLayerRow,palette),1024))ok=0;}
 if(ok&&(nf_hud_pool_palette(b,b->bytes,8,0)||nf_hud_pool_palette(b,b->bytes-1,9,0)||nf_hud_pool_palette(b,b->bytes,9,160)))ok=0;
 free(a);free(b);return ok;
}
int main(int argc,char**argv){_putenv("NF_TEST_HUD_POOL_PLANES=1");size_t n=160*sizeof(NFHudLayerRow);unsigned char*d=calloc(1,n),*out=malloc(n);CHECK(d&&out);
 for(int k=1;k<argc;k++){FILE*f=fopen(argv[k],"rb");CHECK(f&&fread(d,1,n,f)==n&&fgetc(f)==EOF);fclose(f);CHECK(parity(d,n));}
 /* All four samples equal, every plane differs at an unsampled interior byte. */
 memset(d,0,n);for(unsigned row=0;row<160;row++){NFHudLayerRow*r=(NFHudLayerRow*)d+row;r->refresh=99;r->row=row;r->obj_vram[100]=row;r->palette[100]=row;r->oam[100]=row;}
 CHECK(parity(d,n));NFHudRowPool*p=nf_hud_pool_create(d,n,9);CHECK(p&&p->count==0xa0a0a0&&nf_hud_pool_expand(p,p->bytes,9,out,n)&&!memcmp(d,out,n));free(p);
 printf("SAMPLE_FILTER_FULL_POOL_BYTE_PARITY_AND_UNSAMPLED_COLLISION160=PASS\n");free(d);free(out);return 0;}

