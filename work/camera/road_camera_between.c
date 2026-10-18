#include <stdint.h>
#include <math.h>
extern int nf_road_camera_continuous(const double*,const int32_t*,double*);
static int planar(const int32_t*m){return m&&m[0]==m[8]&&m[2]==-m[6]&&m[1]==0&&m[3]==0&&m[5]==0&&m[7]==0&&m[4]==16384&&(m[0]!=0||m[6]!=0);}
static void rigid(const double*p,const int32_t*m,double angle,double*out){
 double x=p[0]+m[9],z=p[2]+m[11],c=cos(angle),s=sin(angle);out[0]=x*c+z*s;out[1]=p[1]+m[10];out[2]=-x*s+z*c;
}
/* Planar rigid yaw with per-world-point endpoint arithmetic residuals.
 Original Q14 normalization/truncation/wrap preserved at phase endpoints.
 Diagnostic only: validate wrap/visibility/topology over actual pose intervals. */
__declspec(dllexport) int nf_road_camera_between(const double*p,const int32_t*a,const int32_t*b,double phase,double*out){
 if(!p||!out||!planar(a)||!planar(b)||!isfinite(phase)||phase<0||phase>1)return 0;
 if(phase==0)return nf_road_camera_continuous(p,a,out);
 if(phase==1)return nf_road_camera_continuous(p,b,out);
 double original[2][3],ideal[2][3],result[3];if(!nf_road_camera_continuous(p,a,original[0])||!nf_road_camera_continuous(p,b,original[1]))return 0;
 double aa=atan2(a[6],a[0]),ab=atan2(b[6],b[0]),delta=atan2(sin(ab-aa),cos(ab-aa)),angle=aa+phase*delta;
 rigid(p,a,aa,ideal[0]);rigid(p,b,ab,ideal[1]);
 double x=p[0]+a[9]+phase*((double)b[9]-a[9]),z=p[2]+a[11]+phase*((double)b[11]-a[11]);result[0]=x*cos(angle)+z*sin(angle);result[1]=p[1]+a[10]+phase*((double)b[10]-a[10]);result[2]=-x*sin(angle)+z*cos(angle);
 for(unsigned k=0;k<3;k++){result[k]+=(1-phase)*(original[0][k]-ideal[0][k])+phase*(original[1][k]-ideal[1][k]);if(!isfinite(result[k]))return 0;}
 for(unsigned k=0;k<3;k++)out[k]=result[k];
 return 1;
}
