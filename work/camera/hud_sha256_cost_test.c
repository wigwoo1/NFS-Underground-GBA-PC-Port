#include <stdio.h>
#include <windows.h>
#include <bcrypt.h>
#include "hud_row_pool.h"
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed line %u\n",__LINE__);return 1;}}while(0)
static BCRYPT_ALG_HANDLE alg;static ULONG object_size;
static int digest(const void*a,ULONG an,const void*b,ULONG bn,uint8_t out[32]){
 BCRYPT_HASH_HANDLE h=NULL;PUCHAR obj=malloc(object_size);if(!obj)return 0;
 int ok=BCryptCreateHash(alg,&h,obj,object_size,NULL,0,0)==0;
 if(ok)ok=BCryptHashData(h,(PUCHAR)a,an,0)==0;
 if(ok)ok=BCryptHashData(h,(PUCHAR)b,bn,0)==0;
 if(ok)ok=BCryptFinishHash(h,out,32,0)==0;
 if(h&&BCryptDestroyHash(h)!=0)ok=0;
 free(obj);return ok;
}
static double now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart*1000/f.QuadPart;}
int main(int argc,char**argv){CHECK(argc==3);ULONG got=0;CHECK(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,NULL,0)==0&&BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&object_size,sizeof(object_size),&got,0)==0&&got==sizeof(object_size)&&object_size>0);
 const uint8_t known[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};uint8_t hash[32],original[32];CHECK(digest("a",1,"bc",2,hash)&&!memcmp(hash,known,32));
 size_t bytes=160*sizeof(NFHudLayerRow);uint8_t*data=malloc(bytes),*out=malloc(bytes);FILE*f=fopen(argv[1],"rb");CHECK(data&&out&&f&&fread(data,1,bytes,f)==bytes&&fgetc(f)==EOF);fclose(f);_putenv("NF_TEST_HUD_POOL_PLANES=1");NFHudRowPool*p=nf_hud_pool_create(data,bytes,7);CHECK(p&&nf_hud_pool_expand(p,p->bytes,7,out,bytes)&&!memcmp(data,out,bytes));
 uint8_t*b=(uint8_t*)&p->refresh;size_t n=p->bytes-offsetof(NFHudRowPool,refresh);CHECK(n<=ULONG_MAX&&digest(&p->epoch,8,b,(ULONG)n,original));
 char path[1600];snprintf(path,sizeof(path),"%s-message.bin",argv[2]);f=fopen(path,"wb");CHECK(f&&fwrite(&p->epoch,1,8,f)==8&&fwrite(b,1,n,f)==n&&fclose(f)==0);snprintf(path,sizeof(path),"%s-digest.bin",argv[2]);f=fopen(path,"wb");CHECK(f&&fwrite(original,1,32,f)==32&&fclose(f)==0);
 for(unsigned i=0;i<96;i++){size_t at=(size_t)i*(n-1)/95;b[at]^=1;CHECK(digest(&p->epoch,8,b,(ULONG)n,hash)&&memcmp(hash,original,32));b[at]^=1;}p->epoch^=1;CHECK(digest(&p->epoch,8,b,(ULONG)n,hash)&&memcmp(hash,original,32));p->epoch^=1;
 double elapsed[2]={0};volatile uint64_t sink=0;for(unsigned round=0;round<80;round++)for(unsigned pos=0;pos<2;pos++){unsigned mode=(round+pos)%2;__asm__ __volatile__("" ::: "memory");double t=now();if(mode){CHECK(digest(&p->epoch,8,b,(ULONG)n,hash));elapsed[mode]+=now()-t;CHECK(!memcmp(hash,original,32));sink^=hash[0];}else{uint64_t h=nf_hud_pool_hash(p);elapsed[mode]+=now()-t;CHECK(h==p->hash);sink^=h;}}
 printf("SHA256_ABC_VECTOR_FULL_MESSAGE_EPOCH_AND96_CORRUPTIONS=PASS bytes=%zu iterations=80 fnv_ms=%.6f sha256_ms=%.6f sink=%llu\n",n+8,elapsed[0]/80,elapsed[1]/80,(unsigned long long)sink);CHECK(BCryptCloseAlgorithmProvider(alg,0)==0);free(p);free(data);free(out);return 0;}

