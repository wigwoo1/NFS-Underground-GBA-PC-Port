#include "../hud_text_sdf.h"
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int decode(uint8_t q) { return (int)q - 128; }
static void single_pixel(void) {
    uint8_t mask[25]={0}, sdf[25]={0}; mask[12]=1;
    assert(nf_hud_text_sdf_encode(mask,5,5,sdf,sizeof(sdf)));
    assert(decode(sdf[12])==8);
    assert(decode(sdf[11])==-8);
    assert(decode(sdf[6])==-15);
    assert(decode(sdf[0])<-32);
}
static void preserve_counter(void) {
    uint8_t mask[25], sdf[25]; memset(mask,1,sizeof(mask)); mask[12]=0;
    assert(nf_hud_text_sdf_encode(mask,5,5,sdf,sizeof(sdf)));
    assert(decode(sdf[12])==-8);
    assert(decode(sdf[11])==8);
}
static void empty_and_full_masks(void) {
    uint8_t empty[12]={0}, full[12], sdf[12]; memset(full,1,sizeof(full));
    assert(nf_hud_text_sdf_encode(empty,4,3,sdf,sizeof(sdf)));
    for(unsigned i=0;i<12;i++) assert(sdf[i]==1);
    assert(nf_hud_text_sdf_encode(full,4,3,sdf,sizeof(sdf)));
    assert(sdf[5]>128);
}
static void symmetric_and_translation_invariant(void) {
    uint8_t a[35]={0}, b[35]={0}, x[35], y[35];
    for(unsigned r=1;r<6;r++) for(unsigned c=1;c<3;c++) a[r*5+c]=1;
    for(unsigned r=1;r<6;r++) for(unsigned c=1;c<3;c++) b[r*5+c+1]=1;
    assert(nf_hud_text_sdf_encode(a,5,7,x,sizeof(x)));
    assert(nf_hud_text_sdf_encode(b,5,7,y,sizeof(y)));
    for(unsigned r=0;r<7;r++) for(unsigned c=0;c<3;c++)
        assert(x[r*5+c]==y[r*5+c+1]);
}
static void scaled_distance_uses_output_pixel_units(void) {
    uint8_t mask[25]={0}, source[25], screen[25], untouched[25]; mask[12]=1;
    assert(nf_hud_text_sdf_encode(mask,5,5,source,sizeof(source)));
    assert(nf_hud_text_sdf_encode_scaled(mask,5,5,13.5f,screen,sizeof(screen)));
    assert(screen[12]==236); /* +6.75 output pixels, 1/16-pixel R8 steps */
    assert(screen[11]==20);  /* -6.75 output pixels */
    assert(nf_hud_text_sdf_encode_scaled(mask,5,5,1.0f,untouched,sizeof(untouched)));
    assert(memcmp(source,untouched,sizeof(source))==0);
    memset(untouched,77,sizeof(untouched));
    assert(!nf_hud_text_sdf_encode_scaled(mask,5,5,0.0f,untouched,sizeof(untouched)));
    assert(untouched[0]==77&&untouched[24]==77);
    assert(!nf_hud_text_sdf_encode_scaled(mask,5,5,NAN,untouched,sizeof(untouched)));
    assert(untouched[0]==77&&untouched[24]==77);
}
static uint8_t brute_code(const uint8_t *mask,unsigned w,unsigned h,unsigned x,unsigned y) {
    int inside=mask[y*w+x]!=0,found=0;double best=1.0e30;
    for(int py=-1;py<=(int)h;py++) for(int px=-1;px<=(int)w;px++) {
        int foreground=px>=0&&py>=0&&px<(int)w&&py<(int)h&&mask[(unsigned)py*w+(unsigned)px];
        if(inside?!foreground:foreground) {
            double dx=(double)px-(double)x,dy=(double)py-(double)y,d=dx*dx+dy*dy;
            if(d<best)best=d;
            found=1;
        }
    }
    if(!inside&&!found)return 1;
    double distance=sqrt(best)-0.5;if(!inside)distance=-distance;
    if(distance>7.9375)distance=7.9375;
    if(distance<-8.0)distance=-8.0;
    int code=(int)lrint(128.0+distance*16.0);
    return (uint8_t)(code<0?0:code>255?255:code);
}
static void exact_distance_matches_brute_force(void) {
    uint8_t mask[36],sdf[36];
    for(unsigned bits=0;bits<512;bits++) {
        for(unsigned i=0;i<9;i++)mask[i]=(uint8_t)((bits>>i)&1);
        assert(nf_hud_text_sdf_encode(mask,3,3,sdf,sizeof(sdf)));
        for(unsigned y=0;y<3;y++)for(unsigned x=0;x<3;x++)
            assert(sdf[y*3+x]==brute_code(mask,3,3,x,y));
    }
    uint32_t rng=0x4e465344u;
    for(unsigned trial=0;trial<400;trial++) {
        unsigned w=1+(trial*7u)%6u,h=1+(trial*11u)%6u;
        for(unsigned i=0;i<w*h;i++){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;mask[i]=(uint8_t)(rng&1);}
        assert(nf_hud_text_sdf_encode(mask,w,h,sdf,sizeof(sdf)));
        for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++)
            assert(sdf[y*w+x]==brute_code(mask,w,h,x,y));
    }
}
static void failures_are_atomic(void) {
    uint8_t mask[4]={1,0,0,1}, out[4]={91,92,93,94};
    assert(!nf_hud_text_sdf_encode(mask,2,2,out,3));
    assert(out[0]==91 && out[3]==94);
    assert(!nf_hud_text_sdf_encode(mask,241,1,out,sizeof(out)));
    assert(!nf_hud_text_sdf_encode(mask,0,2,out,sizeof(out)));
}
int main(void) {
    single_pixel(); preserve_counter(); empty_and_full_masks();
    symmetric_and_translation_invariant(); scaled_distance_uses_output_pixel_units(); exact_distance_matches_brute_force(); failures_are_atomic();
    puts("hud text SDF tests passed");
    return 0;
}



