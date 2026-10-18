#include "../hud_text_sdf.h"
#include <stdint.h>
#include <stdio.h>
#include <time.h>
int main(void) {
    enum { W=240,H=160,N=300 };
    static uint8_t mask[W*H],sdf[W*H];
    for(unsigned y=0;y<H;y++)for(unsigned x=0;x<W;x++)
        mask[y*W+x]=(uint8_t)(((x/3+y/5)%11)==0 && (x%7)!=0);
    clock_t begin=clock();volatile unsigned checksum=0;
    for(unsigned i=0;i<N;i++){
        if(!nf_hud_text_sdf_encode(mask,W,H,sdf,sizeof(sdf)))return 2;
        checksum+=sdf[(i*97u)%(W*H)];
    }
    double seconds=(double)(clock()-begin)/CLOCKS_PER_SEC;
    printf("size=%dx%d runs=%d total_ms=%.3f ms_per_refresh=%.4f checksum=%u\n",
           W,H,N,seconds*1000.0,seconds*1000.0/N,checksum);
    return 0;
}
