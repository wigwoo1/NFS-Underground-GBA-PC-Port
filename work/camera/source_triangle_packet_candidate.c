#include <math.h>
#include <stddef.h>
#include <string.h>
/* Source camera-space XYZUV -> clipped projective XYSTRQRGBA triangles.
   Independent of GL, D3D, screen images and game logic timing. */
__declspec(dllexport) int nf_source_triangle_packet(const double*points,unsigned count,const double*projection,const double*color,double*out,unsigned capacity,unsigned*written){
 if(!points||!projection||!color||!out||!written||count<3||count>32)return 1;
 *written=0;
 for(unsigned j=0;j<count*5;j++)if(!isfinite(points[j]))return 1;
 for(unsigned j=0;j<3;j++)if(!isfinite(projection[j]))return 1;
 if(projection[2]<=0)return 1;
 for(unsigned j=0;j<4;j++)if(!isfinite(color[j]))return 1;
 double polygon[64][5];unsigned n=0;
 for(unsigned j=0;j<count;j++){
 const double*a=points+((j+count-1)%count)*5,*b=points+j*5;int ai=a[2]>=64,bi=b[2]>=64;
 if(ai!=bi){double t=(64-a[2])/(b[2]-a[2]);for(unsigned k=0;k<5;k++)polygon[n][k]=a[k]+t*(b[k]-a[k]);polygon[n++][2]=64;}
 if(bi){memcpy(polygon[n++],b,5*sizeof(double));}
 }
 if(n<3)return 0;unsigned need=(n-2)*3;if(capacity<need)return 2;
 unsigned used=0;
 for(unsigned j=1;j+1<n;j++){unsigned indices[3]={0,j,j+1};for(unsigned k=0;k<3;k++){
 const double*p=polygon[indices[k]];double q=1/p[2];double*v=out+used*10;
 v[0]=projection[0]+projection[2]*p[0]*q;v[1]=projection[1]+projection[2]*p[1]*q;
 v[2]=p[3]*q;v[3]=p[4]*q;v[4]=0;v[5]=q;memcpy(v+6,color,4*sizeof(double));
 for(unsigned h=0;h<10;h++)if(!isfinite(v[h]))return 1;used++;
 }}*written=used;return 0;
}
