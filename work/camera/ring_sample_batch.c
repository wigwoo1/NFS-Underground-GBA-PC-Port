#include <stdint.h>
#include <stddef.h>
static int32_t q14(uint32_t v){int64_t s=v<0x80000000u?(int64_t)v:(int64_t)v-0x100000000ll;return (int32_t)(s>=0?s/16384:-((-s+16383)/16384));}
__declspec(dllexport) int nf_portal_transform_batch(const int32_t *points,size_t n,const int32_t *a,const int32_t *b,int32_t *out){
 if(!points||!a||!b||!out||!n||n>32)return 0;
 for(size_t i=0;i<n;i++)for(size_t j=0;j<2;j++){
 const int32_t *m=j?b:a;uint32_t x=(uint32_t)points[i*2]+(uint32_t)m[9],z=(uint32_t)points[i*2+1]+(uint32_t)m[11];
 out[i*4+j*2]=q14(x*(uint32_t)m[0]+z*(uint32_t)m[6]);
 out[i*4+j*2+1]=q14(x*(uint32_t)m[2]+z*(uint32_t)m[8]);
 }return 1;
}

#include <string.h>
static int32_t i32(const unsigned char*p){int32_t v;memcpy(&v,p,4);return v;}
static int16_t i16(const unsigned char*p){int16_t v;memcpy(&v,p,2);return v;}
static uint16_t u16(const unsigned char*p){uint16_t v;memcpy(&v,p,2);return v;}
__declspec(dllexport) int nf_ring_corrections(const unsigned char*ring,const unsigned char*offsets,size_t n,const unsigned char*ac,const unsigned char*bc,const double*endpoints,int32_t*world,double*corrections){
 if(!ring||!offsets||!ac||!bc||!endpoints||!world||!corrections||!n||n>32)return 0;
 int32_t m[24];memcpy(m,ac,48);memcpy(m+12,bc,48);
 for(size_t i=0;i<n;i++){
 int64_t x=i32(ring+i*68),z=i32(ring+i*68+4);
 if(u16(ring+i*68+42)!=65535){x+=i16(offsets+i*32);z+=i16(offsets+i*32+2);}
 if(x<INT32_MIN||x>INT32_MAX||z<INT32_MIN||z>INT32_MAX)return -1;
 world[i*2]=(int32_t)x;world[i*2+1]=(int32_t)z;
 for(size_t j=0;j<2;j++){
 const int32_t *c=m+j*12;const double *e=endpoints+j*12;
 uint32_t wx=(uint32_t)x+(uint32_t)c[9],wz=(uint32_t)z+(uint32_t)c[11];
 int32_t fx=q14(wx*(uint32_t)c[0]+wz*(uint32_t)c[6]),fz=q14(wx*(uint32_t)c[2]+wz*(uint32_t)c[8]);
 double ax=((double)x+e[9])*e[0]+((double)z+e[11])*e[6];
 double az=((double)x+e[9])*e[2]+((double)z+e[11])*e[8];
 corrections[i*4+j*2]=(double)fx-ax;corrections[i*4+j*2+1]=(double)fz-az;
 }
 }return 1;
}

__declspec(dllexport) int nf_sample_ring_points(const int32_t*world,const double*correction,size_t n,const double*camera,double alpha,double*out){
 if(!world||!correction||!camera||!out||!n||n>32)return 0;
 int far=0,wrap=0;
 for(size_t i=0;i<n;i++){
 double x=((double)world[i*2]+camera[9])*camera[0]+((double)world[i*2+1]+camera[11])*camera[6];
 double z=((double)world[i*2]+camera[9])*camera[2]+((double)world[i*2+1]+camera[11])*camera[8];
 x=x+(1-alpha)*correction[i*4]+alpha*correction[i*4+2];
 z=z+(1-alpha)*correction[i*4+1]+alpha*correction[i*4+3];
 out[i*2]=x;out[i*2+1]=z;
 if(z>24575)far=1;
 if(!(x>=-32768&&x<32768&&z>=-32768&&z<32768))wrap=1;
 }
 return far?2:wrap?-1:1;
}
