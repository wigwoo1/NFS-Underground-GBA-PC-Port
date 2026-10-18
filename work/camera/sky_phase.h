#ifndef NF_SKY_PHASE_H
#define NF_SKY_PHASE_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <math.h>
#ifndef NF_SKY_API
#define NF_SKY_API static
#endif
enum {NF_SKY_COPY_BYTES=15136,NF_SKY_ASSET_BYTES=15376,NF_SKY_PACKET_BYTES=15192};
typedef struct {uint64_t epoch;uint32_t refresh,angle,source,origin,destination;int32_t center;const uint8_t*indices;} NFSkyBoundary;
typedef struct {const uint8_t*lower,*upper;double phase,weight;unsigned lower_offset,upper_offset,exact;} NFSkySample;
NF_SKY_API int nf_sky_boundary_decode(const void*data,size_t bytes,NFSkyBoundary*out){
 if(!data||!out||bytes!=NF_SKY_PACKET_BYTES)return 0;
 uint32_t h[14];memcpy(h,data,56);int32_t center=(int32_t)h[12];
 if(h[0]!=0x4b53464e||h[1]!=1||!(h[2]|h[3])||h[6]!=240||h[7]!=64||h[11]!=NF_SKY_COPY_BYTES||h[13]||center<-32768||center>32767||
    h[9]<0x08000000||h[9]>0x0a000000-NF_SKY_ASSET_BYTES||(h[10]!=0x06002940&&h[10]!=0x0600c940))return 0;
 int32_t offset=(int32_t)(((h[5]&16383u)*240u)>>12)%240-center;offset&=~1;
 if(h[8]!=h[9]+(uint32_t)offset)return 0;
 NFSkyBoundary b={(uint64_t)h[2]|((uint64_t)h[3]<<32),h[4],h[5],h[8],h[9],h[10],center,(const uint8_t*)data+56};*out=b;return 1;
}
NF_SKY_API int nf_sky_asset_verify(const NFSkyBoundary*b,const void*asset,size_t bytes){
 if(!b||!asset||bytes!=NF_SKY_ASSET_BYTES||b->center||b->source<b->origin||b->source-b->origin>238)return 0;
 return !memcmp((const uint8_t*)asset+b->source-b->origin,b->indices,NF_SKY_COPY_BYTES);
}
/* mode0 preserves exact original copies at endpoints. mode1 keeps original
   angular fractional phase at endpoints, avoiding scene-boundary phase snaps. */
NF_SKY_API int nf_sky_phase_sample(const NFSkyBoundary*a,const NFSkyBoundary*b,const void*asset,size_t bytes,double alpha,unsigned mode,NFSkySample*out){
 if(!a||!b||!out||mode>1||!isfinite(alpha)||alpha<0||alpha>1||a->epoch!=b->epoch||a->refresh>b->refresh||a->origin!=b->origin||
    !nf_sky_asset_verify(a,asset,bytes)||!nf_sky_asset_verify(b,asset,bytes))return 0;
 if(a->refresh==b->refresh&&(a->angle!=b->angle||a->source!=b->source||memcmp(a->indices,b->indices,NF_SKY_COPY_BYTES)))return 0;
 int delta=(int)((b->angle-a->angle+8192u)&16383u)-8192;
 double expected=delta*(240.0/4096.0);if(fabs(expected)>=120)return 0;
 NFSkySample s={0};
 if(!mode&&(alpha==0||alpha==1)){
  const NFSkyBoundary*chosen=alpha==1?b:a;s.lower=s.upper=chosen->indices;s.phase=chosen->source-chosen->origin;s.exact=1;*out=s;return 1;
 }
 double phase;
 if(mode){double angle=alpha==1?(b->angle&16383u):(a->angle&16383u)+delta*alpha;phase=angle*(240.0/4096.0);}
 else{double lo=a->source-a->origin,hi=b->source-b->origin;double travel=hi-lo+240*nearbyint((expected-(hi-lo))/240);phase=lo+travel*alpha;}
 phase=fmod(phase,240);if(phase<0)phase+=240;
 s.phase=phase;s.lower_offset=(unsigned)floor(phase);s.upper_offset=(s.lower_offset+1)%240;s.weight=phase-s.lower_offset;
 s.lower=(const uint8_t*)asset+s.lower_offset;s.upper=(const uint8_t*)asset+s.upper_offset;*out=s;return 1;
}
#endif
