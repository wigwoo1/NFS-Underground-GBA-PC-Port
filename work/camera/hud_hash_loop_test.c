#include <stdio.h>
#include <windows.h>
#include "hud_row_pool.h"
static __attribute__((noinline)) uint64_t scalar(const uint8_t*b,size_t n,uint64_t epoch){uint64_t h=14695981039346656037ull;for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ull;}h^=epoch;return h*1099511628211ull;}
static __attribute__((noinline)) uint64_t unrolled(const uint8_t*b,size_t n,uint64_t epoch){uint64_t h=14695981039346656037ull;size_t i=0;
#define STEP(k) do{h^=b[i+(k)];h*=1099511628211ull;}while(0)
 for(;n-i>=8;i+=8){STEP(0);STEP(1);STEP(2);STEP(3);STEP(4);STEP(5);STEP(6);STEP(7);}
#undef STEP
 for(;i<n;i++){h^=b[i];h*=1099511628211ull;}h^=epoch;return h*1099511628211ull;}
static double now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart*1000/f.QuadPart;}
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed line %u\n",__LINE__);return 1;}}while(0)
int main(int argc,char**argv){CHECK(argc==2);uint8_t sample[544];for(unsigned i=0;i<sizeof(sample);i++)sample[i]=(i*71+i/7)&255;
 for(unsigned offset=0;offset<16;offset++)for(unsigned length=0;length<=512;length++)CHECK(scalar(sample+offset,length,17)==unrolled(sample+offset,length,17));
 for(unsigned bit=0;bit<64;bit++)CHECK(scalar(sample,513,1ull<<bit)==unrolled(sample,513,1ull<<bit));
 size_t bytes=160*sizeof(NFHudLayerRow);uint8_t*data=malloc(bytes),*out=malloc(bytes);FILE*f=fopen(argv[1],"rb");CHECK(data&&out&&f&&fread(data,1,bytes,f)==bytes&&fgetc(f)==EOF);fclose(f);_putenv("NF_TEST_HUD_POOL_PLANES=1");NFHudRowPool*p=nf_hud_pool_create(data,bytes,7);CHECK(p&&nf_hud_pool_expand(p,p->bytes,7,out,bytes)&&!memcmp(data,out,bytes));
 const uint8_t*b=(const uint8_t*)&p->refresh;size_t n=p->bytes-offsetof(NFHudRowPool,refresh);CHECK(scalar(b,n,7)==p->hash&&unrolled(b,n,7)==p->hash);
 double elapsed[2]={0};volatile uint64_t sink=0;for(unsigned round=0;round<80;round++)for(unsigned pos=0;pos<2;pos++){unsigned mode=(round+pos)%2;__asm__ __volatile__("" ::: "memory");double t=now();uint64_t h=mode?unrolled(b,n,7):scalar(b,n,7);elapsed[mode]+=now()-t;CHECK(h==p->hash);sink^=h;}
 printf("HASH_EXACT offsets16_lengths0to512_epochbits64_fullpool=PASS bytes=%zu iterations=80 scalar_ms=%.6f unrolled_ms=%.6f sink=%llu\n",n,elapsed[0]/80,elapsed[1]/80,(unsigned long long)sink);free(p);free(data);free(out);return 0;}

