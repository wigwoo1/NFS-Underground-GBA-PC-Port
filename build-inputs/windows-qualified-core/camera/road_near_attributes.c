/* Source-attribute correction policy. Enabled only in the opt-in experimental
   live renderer; original integer endpoints and continuous depth-cell extension. */
#include <stdint.h>
#include <math.h>
static int source_project(int depth,const int32_t attributes[2],unsigned shift,unsigned stored_height,unsigned affine,const uint32_t*reciprocal,double out[2]){
 if(depth<1||depth>=32768||shift>10||stored_height<2||(stored_height&1)||affine>1)return 0;
 uint32_t r=reciprocal[depth];if(!r)return 0;
 for(unsigned k=0;k<2;k++){
  uint32_t raw=(uint32_t)attributes[k],scaled=k?raw*stored_height:raw<<shift;
  int32_t word=affine?(int32_t)(scaled<<1):(int32_t)(((int64_t)((int32_t)scaled>>7)*r)>>8);
  double q=affine?65536.0:(double)r,denominator=k?stored_height*.5:(double)(1u<<shift)*.5;
  out[k]=(double)word/q/denominator;
 }
 return 1;
}
/* Uncut corners need the same attribute policy as near-generated corners,
   otherwise entering/leaving clipping introduces a small UV discontinuity. */
__declspec(dllexport) int nf_road_vertex_attributes(double depth,const int32_t attributes[2],unsigned shift,unsigned stored_height,unsigned affine,const uint32_t*reciprocal,double out[2]){
 if(!attributes||!reciprocal||!out||!isfinite(depth)||depth<1||depth>32767)return 0;
 int lo=(int)floor(depth);double t=depth-lo,a[2],b[2],result[2];
 if(!source_project(lo,attributes,shift,stored_height,affine,reciprocal,a))return 0;
 if(t&&!source_project(lo+1,attributes,shift,stored_height,affine,reciprocal,b))return 0;
 for(unsigned k=0;k<2;k++)result[k]=t?a[k]+(b[k]-a[k])*t:a[k];
 out[0]=result[0];out[1]=result[1];return 1;
}
static int near_integer(int z0,int z1,const int32_t attributes[4],unsigned shift,unsigned stored_height,unsigned affine,int near_z,const uint32_t*reciprocal,double out[2]){
 int start=z0<near_z||(z0==near_z&&z1>=near_z);int behind=start?z0:z1,front=start?z1:z0;
 if(behind>near_z||front<near_z||shift>10||stored_height<2||(stored_height&1))return 0;
 unsigned delta=(unsigned)(front-behind);if(delta>=32768||near_z<1||near_z>=32768)return 0;
 uint32_t factor=(uint32_t)(near_z-behind)*reciprocal[delta],r=reciprocal[near_z];
 if(!r)return 0;
 int32_t clipped_attributes[2];
 for(unsigned k=0;k<2;k++){
  uint32_t diff=(uint32_t)attributes[k+2]-(uint32_t)attributes[k];
  uint32_t adjustment=(uint32_t)(((int64_t)(int32_t)diff*factor)>>24);
  clipped_attributes[k]=(int32_t)((uint32_t)attributes[(start?0:2)+k]+(start?adjustment:0u-adjustment));
 }
 return source_project(near_z,clipped_attributes,shift,stored_height,affine,reciprocal,out);
}
/* Bilinear extension agrees at integer endpoint depths without floor steps
   in the returned UVs. Position clipping remains geometric. Caller must
   retain original edge direction and animated offset separately. */
__declspec(dllexport) int nf_road_near_attributes(double z0,double z1,const int32_t attributes[4],unsigned shift,unsigned stored_height,unsigned affine,int near_z,const uint32_t*reciprocal,double out[2]){
 if(!attributes||!reciprocal||!out||!isfinite(z0)||!isfinite(z1)||z0<-32768||z0>32767||z1<-32768||z1>32767||!((z0<near_z&&z1>=near_z)||(z1<near_z&&z0>=near_z)))return 0;
 int a=(int)floor(z0),b=(int)floor(z1);double tx=z0-a,ty=z1-b,result[2]={0,0};
 for(unsigned i=0;i<2;i++)for(unsigned j=0;j<2;j++){
  double weight=(i?tx:1-tx)*(j?ty:1-ty);if(!weight)continue;
  double corner[2];if(!near_integer(a+(int)i,b+(int)j,attributes,shift,stored_height,affine,near_z,reciprocal,corner))return 0;
  for(unsigned k=0;k<2;k++)result[k]+=weight*corner[k];
 }
 out[0]=result[0];out[1]=result[1];return 1;
}
