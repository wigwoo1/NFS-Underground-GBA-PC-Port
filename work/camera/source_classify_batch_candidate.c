#include <stdint.h>
#include <math.h>
__declspec(dllexport) int nf_source_classify(const double*p,unsigned nv,const uint32_t*off,const uint32_t*ids,unsigned nf,unsigned ni,const double*ra,const double*rb,const double*pa,const double*pb,double alpha,const double*rect,uint8_t*faces,uint8_t*codes){
 if(!p||!off||!ids||!ra||!rb||!pa||!pb||!rect||!faces||!codes||!nv||nv>65536||nf>32768||ni>1048576||!isfinite(alpha)||alpha<0||alpha>1||off[0]||off[nf]!=ni)return 1;
 for(unsigned i=0;i<4;i++)if(!isfinite(rect[i]))return 1;
 for(unsigned i=0;i<nv*2;i++)if(!isfinite(p[i])||!isfinite(pa[i])||!isfinite(pb[i])||!isfinite((p[i]+(1-alpha)*pa[i])+alpha*pb[i]))return 1;
 for(unsigned f=0;f<nf;f++){if(off[f+1]<off[f]||off[f+1]>ni||off[f+1]-off[f]<3||off[f+1]-off[f]>32||!isfinite(ra[f])||!isfinite(rb[f]))return 1;}
 for(unsigned i=0;i<ni;i++)if(ids[i]>=nv)return 1;
 for(unsigned f=0;f<nf;f++){
  unsigned a=ids[off[f]]*2,b=ids[off[f]+1]*2,c=ids[off[f]+2]*2;
  double det=(p[b+1]-p[a+1])*(p[c]-p[a])-(p[c+1]-p[a+1])*(p[b]-p[a]);
  faces[f]=((det+(1-alpha)*ra[f])+alpha*rb[f])>-.5;
  unsigned flags=0,inside_x=0,inside_y=0;
  for(unsigned i=off[f];i<off[f+1];i++){unsigned v=ids[i]*2;double x=(p[v]+(1-alpha)*pa[v])+alpha*pb[v],y=(p[v+1]+(1-alpha)*pa[v+1])+alpha*pb[v+1];int ix=rect[0]-.5<=x&&x<rect[2]-.5,iy=rect[1]-.5<=y&&y<rect[3]-.5;inside_x|=ix;inside_y|=iy;if(!ix)flags|=1;if(!iy)flags|=2;}
  codes[f]=inside_x&&inside_y?flags:4;
 }
 return 0;
}
