#include <math.h>
/* Native lighting introduced for narrow spans, also used on wider walls to
   maintain continuity when a projected wall grows/shrinks across that boundary.
   Perspective-correct endpoint intensity at each native pixel center. This is
   not claimed bit-exact to the GBA rasterizer; geometry and palettes are unchanged. */
static int nf_narrow_wall_shades(const double*x,const double*z,const double*shade,int*out,unsigned count){
 if(!out||!count)return 0;
 for(unsigned i=0;i<2;i++)if(!isfinite(x[i])||!isfinite(z[i])||z[i]<=0||!isfinite(shade[i])||shade[i]<0||shade[i]>15)return 0;
 /* Equal endpoint intensity has no perspective gradient. Preserve every
    output column while avoiding redundant divides for flat-lit walls. */
 if(shade[0]==shade[1]){int level=(int)floor(shade[0]+1e-10);if(level<0)level=0;if(level>15)level=15;for(unsigned i=0;i<count;i++)out[i]=level;return 1;}
 for(unsigned i=0;i<count;i++){
  double p=(i+.5)*240/count,t=x[1]==x[0]?.5:(p-x[0])/(x[1]-x[0]);
  if(t<0)t=0;
  if(t>1)t=1;
  double a=(1-t)/z[0],b=t/z[1],value=(a*shade[0]+b*shade[1])/(a+b);
  int level=(int)floor(value+1e-10);out[i]=level<0?0:level>15?15:level;
 }
 return 1;
}
