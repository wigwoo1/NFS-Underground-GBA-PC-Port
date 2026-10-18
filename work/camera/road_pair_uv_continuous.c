#include <stdint.h>
#include <math.h>
#include <string.h>
extern int nf_road_pair_uv(const int32_t*,const int32_t*,unsigned,unsigned,const uint32_t*,int32_t*);
/* Multilinear extension of the verified integer evaluator. No source-cell truncation. */
__declspec(dllexport) int nf_road_pair_uv_continuous(const double a[3],const double b[3],double width,double pair,const uint32_t*t,double out[2]){
 if(!a||!b||!t||!out||!isfinite(width)||!isfinite(pair)||width<1||width>=32767||pair<0||pair>width-1)return 0;
 double values[8]={a[0],a[1],a[2],b[0],b[1],b[2],width,pair},fraction[8],result[2]={0,0};int32_t base[8];unsigned active_mask=0;
 for(unsigned i=0;i<8;i++){
  if(!isfinite(values[i])||values[i]<INT32_MIN||values[i]>=INT32_MAX)return 0;
  base[i]=(int32_t)floor(values[i]);fraction[i]=values[i]-base[i];if(fraction[i])active_mask|=1u<<i;
 }
 for(unsigned mask=0;;mask=(mask-active_mask)&active_mask){
  double weight=1;int32_t corner[8];
  for(unsigned i=0;i<8;i++){unsigned bit=(mask>>i)&1;weight*=bit?fraction[i]:1-fraction[i];corner[i]=base[i]+bit;}
  
  int32_t uv[2];unsigned w=(unsigned)corner[6],position=(unsigned)corner[7];double sample[2];
  if(position<w){
   if(!nf_road_pair_uv(corner,corner+3,w,position,t,uv))return 0;
   sample[0]=uv[0];sample[1]=uv[1];
  }else{
   /* Only the unused corner of the width/pair triangular domain is extended.
      Continue the final integer segment; width one has a constant endpoint. */
   if(position!=w||!nf_road_pair_uv(corner,corner+3,w,w-1,t,uv))return 0;
   int32_t previous[2];if(w>1&&!nf_road_pair_uv(corner,corner+3,w,w-2,t,previous))return 0;
   for(unsigned k=0;k<2;k++)sample[k]=w>1?2.0*uv[k]-previous[k]:uv[k];
  }
  for(unsigned k=0;k<2;k++)result[k]+=weight*sample[k];
  if(mask==active_mask)break;
 }
 if(!isfinite(result[0])||!isfinite(result[1]))return 0;
 memcpy(out,result,sizeof(result));return 1;
}
