#ifndef NF_PC_EMPTY_MODEL_PLANE_H
#define NF_PC_EMPTY_MODEL_PLANE_H
#include <math.h>
#include <string.h>
/* Filled, unsmoothed triangles under the private affine vertex shader.
   Equal-x/equal-y or duplicate-position vertices have no coverage. Keep vertices and draw order;
   coefficients cannot be observed. Other singular/malformed planes reject. */
static int nf_pc_empty_model_plane(const float v[15],float out[11]){
 if(!v||!out)return 0;
 for(unsigned i=0;i<15;i++)if(!isfinite(v[i]))return 0;
 if(!(v[4]>0)||!(v[9]>0)||!(v[14]>0))return 0;
 if(!((v[0]==v[5]&&v[5]==v[10])||(v[1]==v[6]&&v[6]==v[11])||(v[0]==v[5]&&v[1]==v[6])||(v[0]==v[10]&&v[1]==v[11])||(v[5]==v[10]&&v[6]==v[11])))return 0;
 float plane[11]={v[0],v[1],v[2]/v[4],v[3]/v[4],1,0,0,0,0,0,0};
 for(unsigned i=0;i<11;i++)if(!isfinite(plane[i]))return 0;
 memcpy(out,plane,sizeof(plane));return 1;
}
#endif
