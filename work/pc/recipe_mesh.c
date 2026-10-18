#include "recipe_mesh.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
struct NFPCRecipeMesh{uint64_t info[3];float vertices[930];};
static double cross(const double*a,const double*b,const double*c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
NFPCRecipeMesh*nf_pc_recipe_mesh_ring(const double*ring,unsigned count,size_t maximum){
 if(count>64||(!ring&&count)||maximum<sizeof(NFPCRecipeMesh)||maximum>32u*1024*1024)return NULL;
 double values[64][5],area=0;unsigned ids[64];for(unsigned i=0;i<count;i++){const double*v=ring+i*6;for(unsigned k=0;k<6;k++)if(!isfinite(v[k]))return NULL;if(v[2]<64||v[5]<=0)return NULL;values[i][0]=v[0];values[i][1]=v[1];values[i][2]=v[3]*v[5];values[i][3]=v[4]*v[5];values[i][4]=v[5];for(unsigned k=0;k<5;k++)if(fabs(values[i][k])>FLT_MAX)return NULL;if(!((float)values[i][4]>0))return NULL;ids[i]=i;}
 NFPCRecipeMesh*m=calloc(1,sizeof(*m));if(!m)return NULL;m->info[0]=count;m->info[2]=sizeof(*m);if(count<3)return m;
 for(unsigned i=0;i<count;i++){area+=cross((const double[2]){0,0},values[i],values[(i+1)%count]);}
 if(!isfinite(area)){free(m);return NULL;}if(fabs(area)<1e-8)return m;
 unsigned remaining=count,used=0;double sign=area>0?1:-1;
 while(remaining>=3){int found=0;for(unsigned j=0;j<remaining;j++){unsigned prev=(j+remaining-1)%remaining,next=(j+1)%remaining;const double*a=values[ids[prev]],*b=values[ids[j]],*c=values[ids[next]];if(cross(a,b,c)*sign<1e-8)continue;int inside=0;for(unsigned k=0;k<remaining;k++){if(k==prev||k==j||k==next)continue;const double*v=values[ids[k]];if(cross(a,b,v)*sign>1e-8&&cross(b,c,v)*sign>1e-8&&cross(c,a,v)*sign>1e-8){inside=1;break;}}if(inside)continue;const double*t[3]={a,b,c};for(unsigned k=0;k<3;k++)for(unsigned q=0;q<5;q++){if(used>=930){free(m);return NULL;}m->vertices[used++]=(float)t[k][q];}for(unsigned k=j;k+1<remaining;k++)ids[k]=ids[k+1];remaining--;found=1;break;}
 if(!found){/* Remaining collinear source vertices contribute no area. */double rest=0;for(unsigned j=0;j<remaining;j++){const double*a=values[ids[j]],*b=values[ids[(j+1)%remaining]];rest+=a[0]*b[1]-b[0]*a[1];}if(fabs(rest)>1e-8){free(m);return NULL;}break;}}
 m->info[1]=used/5;return m;
}
void nf_pc_recipe_mesh_free(NFPCRecipeMesh*m){free(m);}
int nf_pc_recipe_mesh_info(const NFPCRecipeMesh*m,uint64_t out[3]){if(!m||!out)return 0;memcpy(out,m->info,sizeof(m->info));return 1;}
int nf_pc_recipe_mesh_vertices(const NFPCRecipeMesh*m,const void**out,size_t*n){if(!m||!out||!n)return 0;*out=m->vertices;*n=m->info[1]*20;return 1;}
int nf_pc_recipe_mesh_plane(const NFPCRecipeMesh*m,unsigned triangle,float out[11]){if(!m||!out||triangle>=m->info[1]/3)return 0;const float*v=m->vertices+triangle*15;double x=v[0],y=v[1],bx=v[5]-x,by=v[6]-y,cx=v[10]-x,cy=v[11]-y,det=bx*cy-by*cx,normal=v[4];if(!isfinite(det)||det==0||normal<=0)return 0;float p[11]={(float)x,(float)y};for(unsigned c=0;c<3;c++){double a=v[2+c],b=v[7+c]-a,d=v[12+c]-a;p[2+c]=(float)(a/normal);p[5+c]=(float)((b*cy-d*by)/(det*normal));p[8+c]=(float)((bx*d-cx*b)/(det*normal));if(!isfinite(p[2+c])||!isfinite(p[5+c])||!isfinite(p[8+c]))return 0;}memcpy(out,p,sizeof(p));return 1;}
