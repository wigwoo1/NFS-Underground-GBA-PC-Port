#include "world_mesh.h"
#include "source_road.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <limits.h>
struct NFPCWorldMesh{uint64_t info[16];double camera[96];float vertices[930];};
static double number(const void*p,size_t at){double v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static int32_t integer(const void*p,size_t at){int32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static int pose(const void*p,double out[7]){for(unsigned i=0;i<7;i++){out[i]=number(p,48+i*8);if(!isfinite(out[i]))return 0;}double n=sqrt(out[3]*out[3]+out[4]*out[4]+out[5]*out[5]+out[6]*out[6]);if(!isfinite(n)||n<1e-10)return 0;for(unsigned i=3;i<7;i++)out[i]/=n;return 1;}
static void rotate(const double q[7],double v[3]){double tx=2*(q[4]*v[2]-q[5]*v[1]),ty=2*(q[5]*v[0]-q[3]*v[2]),tz=2*(q[3]*v[1]-q[4]*v[0]);double r[3]={v[0]+q[6]*tx+q[4]*tz-q[5]*ty,v[1]+q[6]*ty+q[5]*tx-q[3]*tz,v[2]+q[6]*tz+q[3]*ty-q[4]*tx};memcpy(v,r,sizeof(r));}
static double cross(const double*a,const double*b,const double*c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
NFPCWorldMesh* nf_pc_world_mesh(const NFPCWorld*w,unsigned surface,size_t maximum){uint64_t meta[12],wi[4];const void*points,*uv,*attrs,*camera,*table,*bounds,*model;size_t pn,un,an,cn,tn,bn,mn;
 if(maximum<sizeof(NFPCWorldMesh)||maximum>32u*1024*1024||!nf_pc_world_info(w,wi)||!nf_pc_world_surface_info(w,surface,meta)||!nf_pc_world_surface_buffer(w,surface,0,&points,&pn)||!nf_pc_world_surface_buffer(w,surface,1,&uv,&un)||!nf_pc_world_surface_buffer(w,surface,7,&attrs,&an)||!nf_pc_world_surface_buffer(w,surface,8,&camera,&cn)||!nf_pc_world_buffer(w,0,&table,&tn)||!nf_pc_world_buffer(w,1,&bounds,&bn)||!nf_pc_world_model(w,0,&model,&mn)||mn<160||tn!=131072)return NULL;
 double cx=number(model,24),cy=number(model,32),scale=number(model,40),q[7];if(!isfinite(cx)||!isfinite(cy)||!isfinite(scale)||scale<=0||!pose(model,q))return NULL;
 for(unsigned i=1;i<wi[1];i++){const void*other;size_t bytes;if(!nf_pc_world_model(w,i,&other,&bytes)||bytes<104||memcmp((const unsigned char*)model+24,(const unsigned char*)other+24,80))return NULL;}
 int affine=meta[4]==4||meta[4]==6||meta[4]==10,source_camera=cn!=0;int32_t projection[3]={0};
 if(source_camera){double values[3]={cx,cy,scale};for(unsigned i=0;i<3;i++){if(values[i]<INT32_MIN||values[i]>INT32_MAX||values[i]!=trunc(values[i]))return NULL;projection[i]=(int32_t)values[i];}if(bn&&number(bounds,8)!=0)return NULL;}
 unsigned count=(unsigned)meta[0];if(pn!=count*24||un!=count*16||count>32)return NULL;
 NFPCWorldMesh*m=calloc(1,sizeof(*m));if(!m)return NULL;memcpy(m->info,meta,sizeof(meta));m->info[13]=affine;m->info[14]=source_camera;m->info[15]=sizeof(*m);
 double input[32][5],world[32][3],clipped[64][5],projected[64][6];unsigned n=0;
 for(unsigned i=0;i<count;i++){double v[3];for(unsigned k=0;k<3;k++){world[i][k]=number(points,i*24+k*8);v[k]=world[i][k]-q[k];}if(source_camera){if(!nf_pc_road_camera(camera,cn,world[i],v))goto fail;}else rotate(q,v);for(unsigned k=0;k<3;k++){if(!isfinite(v[k]))goto fail;m->camera[i*3+k]=v[k];input[i][k]=v[k];}input[i][3]=number(uv,i*16);input[i][4]=number(uv,i*16+8);}
 if(source_camera){if(!nf_pc_road_project_ring(table,&world[0][0],count,attrs,an,camera,cn,projection,clipped,&n))goto fail;}
 else if(an){if(!nf_pc_road_clip(table,m->camera,count,attrs,an,clipped,&n))goto fail;}
 else for(unsigned i=0;i<count;i++){const double*a=input[(i+count-1)%count],*b=input[i];int ai=a[2]>=64,bi=b[2]>=64;if(ai!=bi){double t=(64-a[2])/(b[2]-a[2]);for(unsigned k=0;k<5;k++)clipped[n][k]=a[k]+(b[k]-a[k])*t;clipped[n++][2]=64;}if(bi)memcpy(clipped[n++],b,5*sizeof(double));}
 unsigned ids[64];double area=0;for(unsigned i=0;i<n;i++){double*v=clipped[i];if(source_camera){if(!(v[2]>0))goto fail;double z=16777216.0/v[2],r=affine?65536:v[2],u=v[3]/(r*meta[1]*.5)+integer(attrs,24)/(256.0*meta[1]),tv=v[4]/(r*meta[2])+integer(attrs,28)/(512.0*meta[2]);double p[6]={v[0],v[1],z,u,tv,1/z};memcpy(projected[i],p,sizeof(p));}else{double reciprocal=1/v[2],p[6]={cx+scale*v[0]*reciprocal,cy+scale*v[1]*reciprocal,v[2],v[3],v[4],reciprocal};memcpy(projected[i],p,sizeof(p));}ids[i]=i;}
 for(unsigned i=0;i<n;i++){area+=projected[i][0]*projected[(i+1)%n][1]-projected[(i+1)%n][0]*projected[i][1];}if(!isfinite(area))goto fail;
 double sign=area>=0?1:-1;unsigned used=0,remaining=n;
 while(remaining>=3){int found=0;for(unsigned j=0;j<remaining;j++){unsigned previous=(j+remaining-1)%remaining,next=(j+1)%remaining;const double*a=projected[ids[previous]],*b=projected[ids[j]],*c=projected[ids[next]];if(cross(a,b,c)*sign<1e-8)continue;int inside=0;for(unsigned k=0;k<remaining;k++){if(k==previous||k==j||k==next)continue;const double*v=projected[ids[k]];if(cross(a,b,v)*sign>1e-8&&cross(b,c,v)*sign>1e-8&&cross(c,a,v)*sign>1e-8){inside=1;break;}}if(inside)continue;
 const double*triangle[3]={a,b,c};for(unsigned k=0;k<3;k++){const double*v=triangle[k];double reciprocal=affine?1:v[5],values[5]={v[0],v[1],v[3]*reciprocal,v[4]*reciprocal,reciprocal};for(unsigned channel=0;channel<5;channel++){if(!isfinite(values[channel])||fabs(values[channel])>FLT_MAX||used>=930)goto fail;m->vertices[used++]=(float)values[channel];}}
 for(unsigned k=j;k+1<remaining;k++){ids[k]=ids[k+1];}remaining--;found=1;break;}if(!found)break;}
 m->info[12]=used/5;return m;
fail:free(m);return NULL;}
void nf_pc_world_mesh_free(NFPCWorldMesh*m){free(m);}
int nf_pc_world_mesh_info(const NFPCWorldMesh*m,uint64_t out[16]){if(!m||!out)return 0;memcpy(out,m->info,sizeof(m->info));return 1;}
int nf_pc_world_mesh_buffer(const NFPCWorldMesh*m,unsigned kind,const void**p,size_t*n){if(!m||kind>1||!p||!n)return 0;*p=kind?(const void*)m->camera:(const void*)m->vertices;*n=kind?(size_t)m->info[0]*24:(size_t)m->info[12]*20;return 1;}
int nf_pc_world_mesh_plane(const NFPCWorldMesh*m,unsigned triangle,float out[11]){if(!m||!out||triangle>=m->info[12]/3)return 0;const float*v=m->vertices+triangle*15;double x=v[0],y=v[1],bx=v[5]-x,by=v[6]-y,cx=v[10]-x,cy=v[11]-y,det=bx*cy-by*cx,normal=v[4];if(!isfinite(det)||det==0||!(normal>0))return 0;float plane[11];plane[0]=(float)x;plane[1]=(float)y;for(unsigned c=0;c<3;c++){double a=v[2+c],b=v[7+c]-a,d=v[12+c]-a;plane[2+c]=(float)(a/normal);plane[5+c]=(float)((b*cy-d*by)/(det*normal));plane[8+c]=(float)((bx*d-cx*b)/(det*normal));if(!isfinite(plane[2+c])||!isfinite(plane[5+c])||!isfinite(plane[8+c]))return 0;}memcpy(out,plane,sizeof(plane));return 1;}

