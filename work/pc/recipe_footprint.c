#include "recipe_footprint.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
struct NFPCRecipeFootprint{uint64_t info[6];double normal[3],point[3],translation[3],rotation[4],inverse[4],projection[3];};
static double dot(const double*a,const double*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
NFPCRecipeFootprint*nf_pc_recipe_footprint_create(const NFPCRecipeGeometry*g,uint64_t ordinal,unsigned write,const double projection[3],size_t maximum){
 uint64_t gi[9];const void*raw,*matrix;size_t bytes,mn;
 if(!ordinal||ordinal>INT64_MAX||!projection||!isfinite(projection[0])||!isfinite(projection[1])||!isfinite(projection[2])||projection[2]<=0||maximum<sizeof(NFPCRecipeFootprint)||maximum>64u*1024*1024||!nf_pc_recipe_geometry_info(g,gi)||write<gi[1]||gi[3]<3||gi[3]>32||!nf_pc_recipe_geometry_buffer(g,0,&raw,&bytes)||bytes!=gi[3]*24||!nf_pc_recipe_geometry_buffer(g,3,&matrix,&mn)||mn!=48)return NULL;
 const double*v=raw;NFPCRecipeFootprint result;memset(&result,0,sizeof(result));double largest=0;
 for(unsigned i=1;i<gi[3];i++)for(unsigned j=i+1;j<gi[3];j++){double a[3],b[3],c[3];for(unsigned k=0;k<3;k++){a[k]=v[i*3+k]-v[k];b[k]=v[j*3+k]-v[k];}c[0]=a[1]*b[2]-a[2]*b[1];c[1]=a[2]*b[0]-a[0]*b[2];c[2]=a[0]*b[1]-a[1]*b[0];double length=dot(c,c);if(length>largest){largest=length;memcpy(result.normal,c,sizeof(c));}}
 if(!isfinite(largest)||largest<=1e-20)return NULL;
 for(unsigned k=0;k<3;k++){result.normal[k]/=sqrt(largest);result.point[k]=v[k];}
 for(unsigned i=0;i<gi[3];i++){double delta[3];for(unsigned k=0;k<3;k++)delta[k]=v[i*3+k]-v[k];if(fabs(dot(delta,result.normal))>1e-6)return NULL;}
 int32_t m[12];memcpy(m,matrix,48);result.rotation[0]=m[0]/16384.;result.rotation[1]=m[6]/16384.;result.rotation[2]=m[2]/16384.;result.rotation[3]=m[8]/16384.;double determinant=result.rotation[0]*result.rotation[3]-result.rotation[1]*result.rotation[2];if(!isfinite(determinant)||fabs(determinant)<1e-12)return NULL;
 result.inverse[0]=result.rotation[3]/determinant;result.inverse[1]=-result.rotation[1]/determinant;result.inverse[2]=-result.rotation[2]/determinant;result.inverse[3]=result.rotation[0]/determinant;for(unsigned k=0;k<3;k++)result.translation[k]=m[9+k];memcpy(result.projection,projection,24);uint64_t info[6]={gi[0],gi[2],ordinal,gi[1],write,sizeof(result)};memcpy(result.info,info,sizeof(info));NFPCRecipeFootprint*f=malloc(sizeof(*f));if(f)memcpy(f,&result,sizeof(result));return f;
}
void nf_pc_recipe_footprint_free(NFPCRecipeFootprint*f){free(f);}
int nf_pc_recipe_footprint_info(const NFPCRecipeFootprint*f,uint64_t out[6]){if(!f||!out)return 0;memcpy(out,f->info,sizeof(f->info));return 1;}
int nf_pc_recipe_footprint_lift(const NFPCRecipeFootprint*f,double x,double y,double out[4]){
 if(!f||!out||!isfinite(x)||!isfinite(y))return 0;
 double rx=(x-f->projection[0])/f->projection[2],ry=(y-f->projection[1])/f->projection[2],direction[3]={f->inverse[0]*rx+f->inverse[1],ry,f->inverse[2]*rx+f->inverse[3]},point[3];for(unsigned k=0;k<3;k++)point[k]=f->point[k]+f->translation[k];double den=dot(direction,f->normal);if(!isfinite(den)||fabs(den)<1e-12)return 0;double depth=dot(point,f->normal)/den,result[4];if(!isfinite(depth)||depth<=0)return 0;for(unsigned k=0;k<3;k++){result[k]=-f->translation[k]+depth*direction[k];if(!isfinite(result[k]))return 0;}result[3]=depth;memcpy(out,result,sizeof(result));return 1;
}
int nf_pc_recipe_footprint_source(const NFPCRecipeFootprint*f,const double world[3],double out[3]){
 if(!f||!world||!out)return 0;
 double p[3];for(unsigned k=0;k<3;k++){if(!isfinite(world[k]))return 0;p[k]=world[k]+f->translation[k];}double x=f->rotation[0]*p[0]+f->rotation[1]*p[2],z=f->rotation[2]*p[0]+f->rotation[3]*p[2];if(!isfinite(z)||z<=0)return 0;double result[3]={f->projection[0]+f->projection[2]*x/z,f->projection[1]+f->projection[2]*p[1]/z,z};for(unsigned k=0;k<3;k++)if(!isfinite(result[k]))return 0;memcpy(out,result,sizeof(result));return 1;
}
static int key(const uint64_t*k){return k&&k[0]&&k[0]<=INT64_MAX&&k[1]&&k[1]<=UINT32_MAX&&k[2]<=k[3]&&k[3]<=UINT32_MAX&&k[4]<=1;}
int nf_pc_recipe_footprint_sample(const NFPCRecipeFootprint*f,const uint64_t a[5],const NFRigidPose*ca,const uint64_t b[5],const NFRigidPose*cb,double alpha,double x,double y,double out[3]){
 if(!f||!key(a)||!key(b)||a[0]!=f->info[0]||b[0]!=a[0]||b[1]<=a[1]||b[3]<=a[3]||b[3]-a[3]>8||!isfinite(alpha)||alpha<0||alpha>1||f->info[4]>(alpha==1?b[3]:a[3])||!ca||!cb||!out)return 0;
 double lifted[4];if(!nf_pc_recipe_footprint_lift(f,x,y,lifted))return 0;NFRigidPose identity={{0,0,0},{0,0,0,1}};NFPoint3 point={lifted[0],lifted[1],lifted[2]},result;if(!nf_rigid_scene_sample(ca,cb,&identity,&identity,alpha,&point,1,&result))return 0;memcpy(out,&result,24);return 1;
}

int nf_pc_recipe_footprint_lift_pose(const NFPCRecipeFootprint*f,const NFRigidPose*pose,double x,double y,double out[4]){
 if(!f||!pose||!out||!isfinite(x)||!isfinite(y))return 0;
 NFRigidPose normalized;if(!nf_pose_sample(pose,pose,0,&normalized))return 0;double position[3]={normalized.position.x,normalized.position.y,normalized.position.z};normalized.position=(NFPoint3){0,0,0};NFRigidPose identity={{0,0,0},{0,0,0,1}};NFPoint3 basis[4]={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},camera[4];if(!nf_rigid_scene_sample(&normalized,&normalized,&identity,&identity,0,basis,4,camera))return 0;
 double values[4][3];memcpy(values,camera,sizeof(values));double ray[3]={(x-f->projection[0])/f->projection[2],(y-f->projection[1])/f->projection[2],1},direction[3],origin[3],delta[3];
 for(unsigned k=0;k<3;k++){double column[3];for(unsigned j=0;j<3;j++)column[j]=values[k+1][j]-values[0][j];direction[k]=dot(column,ray);origin[k]=position[k];delta[k]=f->point[k]-origin[k];}
 double denominator=dot(direction,f->normal);if(!isfinite(denominator)||fabs(denominator)<1e-12)return 0;double depth=dot(delta,f->normal)/denominator,result[4];if(!isfinite(depth)||depth<=0)return 0;
 for(unsigned k=0;k<3;k++){result[k]=origin[k]+direction[k]*depth;if(!isfinite(result[k]))return 0;}result[3]=depth;memcpy(out,result,sizeof(result));return 1;
}
int nf_pc_recipe_footprint_sample_anchored(const NFPCRecipeFootprint*f,const uint64_t owner[5],const uint64_t a[5],const NFRigidPose*ca,const uint64_t b[5],const NFRigidPose*cb,double alpha,double x,double y,double out[3]){
 if(!f||!key(owner)||!key(a)||!key(b)||a[0]!=f->info[0]||b[0]!=a[0]||b[1]<=a[1]||b[3]<=a[3]||b[3]-a[3]>8||!isfinite(alpha)||alpha<0||alpha>1||!ca||!cb||!out)return 0;
 int older=!memcmp(owner,a,40),newer=!memcmp(owner,b,40);if((!older&&!newer)||(newer&&alpha!=1)||f->info[4]>owner[3])return 0;
 double lifted[4];if(!nf_pc_recipe_footprint_lift_pose(f,older?ca:cb,x,y,lifted))return 0;NFRigidPose identity={{0,0,0},{0,0,0,1}};NFPoint3 point={lifted[0],lifted[1],lifted[2]},result;if(!nf_rigid_scene_sample(ca,cb,&identity,&identity,alpha,&point,1,&result))return 0;memcpy(out,&result,24);return 1;
}
