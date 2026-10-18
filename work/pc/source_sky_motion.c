#include "source_sky_motion.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
struct NFPCSkyMotion{uint64_t info[7];uint32_t angle[2],destination[2],offset[2];int delta;unsigned char asset[15376];};
static unsigned offset(unsigned angle){return (((angle&16383u)*240u/4096u)%240u)&~1u;}
static int boundary(const void*data,size_t n,const uint64_t key[5],uint32_t out[14]){
 if(!data||n!=30568||!key||!key[0]||!key[1]||key[1]>UINT32_MAX||key[2]>key[3]||key[3]>UINT32_MAX||key[4]>1)return 0;
 memcpy(out,data,56);uint64_t epoch=(uint64_t)out[2]|((uint64_t)out[3]<<32);
 if(out[0]!=0x4b53464e||out[1]!=1||epoch!=key[0]||out[4]<key[2]||out[4]>key[3]||out[6]!=240||out[7]!=64||out[11]!=15136||out[12]||out[13]||out[9]<0x08000000||out[9]>0x0a000000-15376||out[10]!=0x06002940u+key[4]*0xa000u)return 0;
 unsigned phase=offset(out[5]);if(out[8]!=out[9]+phase||memcmp((const unsigned char*)data+56,(const unsigned char*)data+15192+phase,15136))return 0;
 return 1;
}
NFPCSkyMotion* nf_pc_sky_motion_decode(const void*a,size_t an,const uint64_t ak[5],const void*b,size_t bn,const uint64_t bk[5],size_t maximum){
 if(maximum<sizeof(NFPCSkyMotion)||maximum>64u*1024||!ak||!bk||ak[0]!=bk[0]||ak[1]>=bk[1]||ak[3]>=bk[3]||bk[3]-ak[3]>8)return NULL;
 uint32_t x[14],y[14];if(!boundary(a,an,ak,x)||!boundary(b,bn,bk,y)||x[4]>=y[4]||x[9]!=y[9]||memcmp((const unsigned char*)a+15192,(const unsigned char*)b+15192,15376))return NULL;
 int delta=(int)(((y[5]&16383u)-(x[5]&16383u)+8192u)&16383u)-8192;if(fabs(delta*240.0/4096)>=120)return NULL;
 NFPCSkyMotion*p=calloc(1,sizeof(*p));if(!p)return NULL;p->info[0]=ak[0];p->info[1]=x[4];p->info[2]=y[4];p->info[3]=x[5];p->info[4]=y[5];p->info[5]=x[9];p->info[6]=sizeof(*p);p->delta=delta;
 p->angle[0]=x[5];p->angle[1]=y[5];p->destination[0]=x[10];p->destination[1]=y[10];p->offset[0]=offset(x[5]);p->offset[1]=offset(y[5]);memcpy(p->asset,(const unsigned char*)a+15192,15376);return p;
}
void nf_pc_sky_motion_free(NFPCSkyMotion*p){free(p);}
int nf_pc_sky_motion_info(const NFPCSkyMotion*p,uint64_t out[7]){if(!p||!out)return 0;memcpy(out,p->info,sizeof(p->info));return 1;}
int nf_pc_sky_motion_sample(const NFPCSkyMotion*p,double alpha,unsigned mode,void*lower,size_t ln,void*upper,size_t un,double*weight,uint32_t*destination){
 if(!p||!lower||!upper||ln<15136||un<15136||!weight||!destination||mode>1||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 uintptr_t lo=(uintptr_t)lower,up=(uintptr_t)upper;if(lo>UINTPTR_MAX-15136||up>UINTPTR_MAX-15136||(lo<up+15136&&up<lo+15136))return 0;
 double phase;if(mode==NFPC_SKY_CONTINUOUS_PHASE)phase=((p->angle[0]&16383u)+p->delta*alpha)*240.0/4096;
 else{double expected=p->delta*240.0/4096;int difference=(int)p->offset[1]-(int)p->offset[0];double travel=difference+240*round((expected-difference)/240);phase=p->offset[0]+travel*alpha;}
 phase=fmod(phase,240);if(phase<0)phase+=240;unsigned base=(unsigned)floor(phase),next=(base+1)%240;double w=phase-base;
 if(mode==NFPC_SKY_EXACT_ENDPOINTS&&(alpha==0||alpha==1)){base=p->offset[alpha==1];next=base;w=0;}
 memcpy(lower,p->asset+base,15136);memcpy(upper,p->asset+next,15136);*weight=w;*destination=p->destination[alpha==1];return 1;
}
