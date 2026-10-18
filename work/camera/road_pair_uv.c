#include <stdint.h>
#include <string.h>
static int unproject(int32_t q,int32_t value,const uint32_t*t,int32_t*out){
 int32_t index=q>>4;if(index<0||index>=32768)return 0;
 uint32_t product=t[index]*(uint32_t)(value>>8);*out=(int32_t)product>>4;return 1;
}
/* Boundary arrays U,V,Q; original pair width and zero-based pair index. */
__declspec(dllexport) int nf_road_pair_uv(const int32_t a[3],const int32_t b[3],unsigned width,unsigned pair,const uint32_t*t,int32_t out[2]){
 if(!a||!b||!t||!out||!width||width>=32768||pair>=width)return 0;
 uint32_t inverse=t[width]>>8;int32_t result[2];
 if(width<=32){
  for(unsigned k=0;k<2;k++){
   int32_t l,r;if(!unproject(a[2],a[k],t,&l)||!unproject(b[2],b[k],t,&r))return 0;
   int32_t diff=(int32_t)((uint32_t)r-(uint32_t)l);int32_t step=(int32_t)((uint32_t)(diff>>8)*inverse)>>8;
   result[k]=(int32_t)((uint32_t)l+pair*(uint32_t)step);
  }
 }else{
  unsigned block=pair/16,within=pair%16;int32_t diffq=(int32_t)((uint32_t)b[2]-(uint32_t)a[2]);int32_t dq=(int32_t)(uint32_t)((uint64_t)((int64_t)diffq*inverse)>>12);
  for(unsigned k=0;k<2;k++){
   int32_t diff=(int32_t)((uint32_t)b[k]-(uint32_t)a[k]);int32_t step=(int32_t)((uint32_t)(diff>>8)*inverse)>>4;int32_t values[2];
   for(unsigned j=0;j<2;j++){
    int32_t q=(int32_t)((uint32_t)a[2]+(block+j)*(uint32_t)dq),uv=(int32_t)((uint32_t)a[k]+(block+j)*(uint32_t)step);
    if(!unproject(q,uv,t,values+j))return 0;
   }
   diff=(int32_t)((uint32_t)values[1]-(uint32_t)values[0]);result[k]=(int32_t)((uint32_t)values[0]+within*(uint32_t)(diff>>4));
  }
 }
 memcpy(out,result,sizeof(result));return 1;
}
