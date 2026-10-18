#include "recipe_geometry.h"
#include "source_road.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
struct NFPCRecipeGeometry {uint64_t info[9];double world[96],uv[64];uint8_t attributes[288],matrix[48],bounds[8];};
static uint32_t u32(const void*p,unsigned at){uint32_t v;memcpy(&v,(const uint8_t*)p+at,4);return v;}
static int32_t s32(const void*p,unsigned at){int32_t v;memcpy(&v,(const uint8_t*)p+at,4);return v;}
static uint16_t u16(const void*p,unsigned at){uint16_t v;memcpy(&v,(const uint8_t*)p+at,2);return v;}
static int16_t s16(const void*p,unsigned at){int16_t v;memcpy(&v,(const uint8_t*)p+at,2);return v;}
NFPCRecipeGeometry*nf_pc_recipe_geometry_decode(uint64_t epoch,unsigned refresh,unsigned kind,const NFRecipeBlock*b,unsigned count,size_t maximum){
 if(!epoch||epoch>INT64_MAX||!refresh||(kind!=1&&kind!=2)||!b||count!=12||maximum<sizeof(NFPCRecipeGeometry)||maximum>64u*1024*1024)return NULL;
 for(unsigned i=0;i<12;i++)if(!b[i].data||!b[i].bytes||b[i].bytes>0x100000)return NULL;
 NFPCRecipeGeometry result;memset(&result,0,sizeof(result));result.info[0]=epoch;result.info[1]=refresh;result.info[2]=kind;result.info[8]=sizeof(result);
 if(kind==1){
  const unsigned fixed[10]={20,48,48,8,32,0,512,48,64,64};for(unsigned i=2;i<12;i++)if(fixed[i-2]&&b[i].bytes!=fixed[i-2])return NULL;
  const void*config=b[6].data,*material=b[3].data;unsigned n=u32(config,0),affine=u32(config,4),shift=u16(material,36),height=u16(material,38);if(n<3||n>32||affine>1||shift>10||!height||height>1024||b[0].bytes!=n*68||b[1].bytes!=n*32)return NULL;
  uint32_t raw[72]={n,shift,height,affine,0,0,(uint32_t)s32(config,24),(uint32_t)s32(config,28)};result.info[3]=n;result.info[4]=1u<<shift;result.info[5]=height/2;result.info[6]=affine;result.info[7]=height>=2&&!(height&1);
  for(unsigned i=0;i<n;i++){const uint8_t*v=(const uint8_t*)b[0].data+i*68,*o=(const uint8_t*)b[1].data+i*32;result.world[i*3]=(double)s32(v,0)+s16(o,0);result.world[i*3+1]=(double)s16(v,56)+s16(o,6)+s16(b[2].data,6);result.world[i*3+2]=(double)s32(v,4)+s16(o,2);raw[8+i*2]=u32(v,32);raw[9+i*2]=u32(v,36);result.uv[i*2]=s32(v,32)/16384.0+s32(config,24)/(256.0*(1u<<shift));result.uv[i*2+1]=s32(v,36)/16384.0+s32(config,28)/(256.0*height);}
  memcpy(result.attributes,raw,288);memcpy(result.matrix,b[4].data,48);memcpy(result.bounds,b[5].data,8);
 }else{
  const unsigned fixed[12]={136,64,8,48,48,8,64,32,65536,512,52,260};for(unsigned i=0;i<12;i++)if(b[i].bytes!=fixed[i])return NULL;
  const void*v=b[0].data,*o=b[1].data,*material=b[4].data,*animation=b[2].data;unsigned flags=u32(b[11].data,256),shift=u16(material,36),height=u16(material,38);if(flags>65535||shift>10||!height||height>1024)return NULL;
  double x=(double)s32(v,0)+s16(o,0),z=(double)s32(v,4)+s16(o,2),nx=(double)s32(v,68)+s16(o,32),nz=(double)s32(v,72)+s16(o,34);double points[12]={x,(double)s16(v,8)+s16(o,8),z,nx,(double)s16(v,12)+s16(o,8),nz,nx,(double)s16(v,14)+s16(o,10),nz,x,(double)s16(v,10)+s16(o,10),z};memcpy(result.world,points,sizeof(points));
  result.info[3]=4;result.info[4]=1u<<shift;result.info[5]=height;result.info[6]=flags;result.info[7]=!(flags&128)&&((uint64_t)(1u<<shift)*height<=65536);
  if(result.info[7]){double start=u16(v,40)/(double)(1u<<shift)+s16(animation,4)/(256.0*(1u<<shift)),end=start+u16(v,64)/256.0;if(flags&2){double t=start;start=end;end=t;}int32_t a=s16(animation,6);a=a>=0?a/2:-((-a+1)/2);double top=((double)s32(v,16)+a)/(128.0*height),span=((double)s32(v,24)+a)/(128.0*height);double uv[8]={start,top,end,top,end,top+span,start,top+span};memcpy(result.uv,uv,sizeof(uv));}
  memcpy(result.matrix,b[3].data,48);memcpy(result.bounds,b[5].data,8);
 }
 const uint16_t*clip=(const uint16_t*)result.bounds;if(clip[0]>clip[1]||clip[1]>240||clip[2]>clip[3]||clip[3]>160)return NULL;
 NFPCRecipeGeometry*g=malloc(sizeof(*g));if(g)memcpy(g,&result,sizeof(result));return g;
}
void nf_pc_recipe_geometry_free(NFPCRecipeGeometry*g){free(g);}
int nf_pc_recipe_geometry_info(const NFPCRecipeGeometry*g,uint64_t out[9]){if(!g||!out)return 0;memcpy(out,g->info,sizeof(g->info));return 1;}
int nf_pc_recipe_geometry_buffer(const NFPCRecipeGeometry*g,unsigned kind,const void**out,size_t*bytes){if(!g||kind>4||!out||!bytes)return 0;const void*p[]={g->world,g->uv,g->attributes,g->matrix,g->bounds};size_t n[]={g->info[3]*24,g->info[7]?g->info[3]*16:0,g->info[2]==1?288:0,48,8};*out=p[kind];*bytes=n[kind];return 1;}
static int key(const uint64_t*k){return k&&k[0]&&k[0]<=INT64_MAX&&k[1]&&k[1]<=UINT32_MAX&&k[2]<=k[3]&&k[3]<=UINT32_MAX&&k[4]<=1;}
int nf_pc_recipe_geometry_camera(const NFPCRecipeGeometry*g,const uint64_t a[5],const NFRigidPose*ca,const uint64_t b[5],const NFRigidPose*cb,double alpha,void*out,size_t bytes){
 if(!g||!key(a)||!key(b)||a[0]!=g->info[0]||b[0]!=a[0]||b[1]<=a[1]||b[3]<=a[3]||b[3]-a[3]>8||g->info[1]>(alpha==1?b[3]:a[3])||!ca||!cb||!isfinite(alpha)||alpha<0||alpha>1||!out||bytes<g->info[3]*24)return 0;
 NFRigidPose identity={{0,0,0},{0,0,0,1}};NFPoint3 result[32];if(!nf_rigid_scene_sample(ca,cb,&identity,&identity,alpha,(const NFPoint3*)g->world,(unsigned)g->info[3],result))return 0;memcpy(out,result,g->info[3]*24);return 1;
}
int nf_pc_recipe_geometry_project(const NFPCRecipeGeometry*g,const uint64_t a[5],const NFRigidPose*ca,const uint64_t b[5],const NFRigidPose*cb,double alpha,const double projection[3],const void*table,size_t tn,void*out,size_t bytes,unsigned*count){
 if(!g||!g->info[7]||!projection||!out||bytes<64u*6*8||!count||!isfinite(projection[0])||!isfinite(projection[1])||!isfinite(projection[2])||projection[2]<=0)return 0;
 double camera[96],clipped[64][5],result[64][6];unsigned n=0,c=(unsigned)g->info[3];if(!nf_pc_recipe_geometry_camera(g,a,ca,b,cb,alpha,camera,sizeof(camera)))return 0;
 if(g->info[2]==1){if(!table||tn!=131072||!nf_pc_road_clip(table,camera,c,g->attributes,288,clipped,&n))return 0;}else for(unsigned i=0;i<c;i++){unsigned j=(i+c-1)%c;const double*x=camera+j*3,*y=camera+i*3;int xi=x[2]>=64,yi=y[2]>=64;if(xi!=yi){double t=(64-x[2])/(y[2]-x[2]);for(unsigned k=0;k<3;k++)clipped[n][k]=x[k]+t*(y[k]-x[k]);clipped[n][2]=64;for(unsigned k=0;k<2;k++)clipped[n][3+k]=g->uv[j*2+k]+t*(g->uv[i*2+k]-g->uv[j*2+k]);n++;}if(yi){memcpy(clipped[n],y,24);memcpy(clipped[n]+3,g->uv+i*2,16);n++;}}
 for(unsigned i=0;i<n;i++){double*z=clipped[i],q=1/z[2];result[i][0]=projection[0]+projection[2]*z[0]*q;result[i][1]=projection[1]+projection[2]*z[1]*q;result[i][2]=z[2];result[i][3]=z[3];result[i][4]=z[4];result[i][5]=(g->info[2]==1&&g->info[6])?1:q;for(unsigned k=0;k<6;k++)if(!isfinite(result[i][k]))return 0;}
 if(n){memcpy(out,result,n*6*8);}
 *count=n;return 1;
}
