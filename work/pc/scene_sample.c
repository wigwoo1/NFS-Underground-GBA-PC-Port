#include "scene_sample_internal.h"
#include "scene_region_pair.h"
#include "scene_pose_sample.h"
#include "source_sky_motion.h"
#include "empty_model_plane.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
static void why(unsigned*p,unsigned v){if(p)*p=v;}
static int room(NFPCSceneSample*p,size_t n,size_t maximum){if(n>maximum-p->info[12])return 0;p->info[12]+=n;return 1;}
static int interval(const NFPCScene*a,const NFPCScene*b,const NFPCSceneRegionPair*pair,double*lo,double*hi,unsigned*reason){
 uint64_t pi[16];if(!nf_pc_scene_region_pair_info(pair,pi)){why(reason,NFPC_SAMPLE_PAIR);return 0;}double first=0,last=0;unsigned found=0;
 for(unsigned i=0;i<pi[6];i++){uint64_t v[9];if(!nf_pc_scene_region_pair_band(pair,i,v)){why(reason,NFPC_SAMPLE_PAIR);return 0;}
  if(v[6]==NFPC_REGION_DISCONTINUITY){why(reason,NFPC_SAMPLE_BREAK);return 0;}if(v[6]!=NFPC_REGION_FORWARD)continue;
  const void*x,*y,*sx,*sy;size_t xn,yn,sxn,syn;uint64_t at[16],bt[16];uint32_t sky_a,sky_b;double alpha;
  if(!nf_pc_scene_motion_timing(a,(unsigned)v[2],&x,&xn)||!nf_pc_scene_motion_timing(b,(unsigned)v[3],&y,&yn)||xn!=184||yn!=184||!nf_pc_scene_motion_sky(a,(unsigned)v[2],&sx,&sxn)||!nf_pc_scene_motion_sky(b,(unsigned)v[3],&sy,&syn)||sxn!=30568||syn!=30568){why(reason,NFPC_SAMPLE_SOURCE);return 0;}
  memcpy(at,x,128);memcpy(bt,y,128);memcpy(&sky_a,(const unsigned char*)sx+16,4);memcpy(&sky_b,(const unsigned char*)sy+16,4);
  if(!nf_pc_scene_pose_alpha(a,(unsigned)v[2],b,(unsigned)v[3],(double)at[6],&alpha)||sky_b<=sky_a){why(reason,NFPC_SAMPLE_TIME);return 0;}
  double left=at[6]>sky_a?(double)at[6]:(double)sky_a,right=bt[6]<sky_b?(double)bt[6]:(double)sky_b;
  if(!found){first=left;last=right;}else{if(left>first)first=left;if(right<last)last=right;}found++;
 }
 if(!found){why(reason,NFPC_SAMPLE_HELD);return 0;}if(first>=last){why(reason,NFPC_SAMPLE_TIME);return 0;}*lo=first;*hi=last;why(reason,NFPC_SAMPLE_OK);return 1;
}
int nf_pc_scene_sample_range(const NFPCScene*a,const NFPCScene*b,double*lo,double*hi,unsigned*reason){
 if(!lo||!hi){why(reason,NFPC_SAMPLE_ARGUMENT);return 0;}NFPCSceneRegionPair*p=nf_pc_scene_region_pair_prepare(a,b,256u*1024);if(!p){why(reason,NFPC_SAMPLE_PAIR);return 0;}int ok=interval(a,b,p,lo,hi,reason);nf_pc_scene_region_pair_free(p);return ok;
}
static int sampled_planes(NFPCSceneSample*p,NFPCSceneSampleDraw*d,size_t maximum){
 uint64_t m[16];size_t vertices,n;const void*v;
 if(d->model){if(!nf_pc_model_mesh_info(d->model,m)||!room(p,(size_t)m[6],maximum)||!nf_pc_model_mesh_buffer(d->model,0,&v,&n))return 0;vertices=(size_t)m[4];}
 else{if(!nf_pc_world_mesh_info(d->world,m)||!room(p,(size_t)m[15],maximum)||!nf_pc_world_mesh_buffer(d->world,0,&v,&n))return 0;vertices=(size_t)m[12];}
 if(vertices%3||n!=vertices*20)return 0;
 size_t bytes=vertices/3*11*sizeof(float);if(!room(p,bytes,maximum))return 0;
 if(bytes){d->planes=malloc(bytes);if(!d->planes)return 0;for(unsigned t=0;t<vertices/3;t++)if(!(d->model?nf_pc_model_mesh_plane(d->model,t,d->planes+t*11):nf_pc_world_mesh_plane(d->world,t,d->planes+t*11))&&!(d->model&&nf_pc_empty_model_plane((const float*)v+t*15,d->planes+t*11)))return 0;}
 d->command.info[5]=vertices;d->command.vertices=v;d->command.vertices_bytes=n;d->command.planes=d->planes;return 1;
}
static int sky_band(NFPCSceneSample*p,const NFPCScene*b,unsigned ar,unsigned br,unsigned top,unsigned bottom,double target,double*alpha){
 const void*a,*z;size_t an,zn;if(!nf_pc_scene_motion_sky(p->base,ar,&a,&an)||!nf_pc_scene_motion_sky(b,br,&z,&zn))return 0;
 NFPCSkyMotion*sky=nf_pc_sky_motion_decode(a,an,p->base->owner[ar],z,zn,b->owner[br],64u*1024);if(!sky)return 0;uint64_t info[7];int ok=0;unsigned char lower[15136],upper[15136];double weight;uint32_t destination;
 if(!nf_pc_sky_motion_info(sky,info)||info[2]<=info[1])goto done;
 *alpha=(target-(double)info[1])/(double)(info[2]-info[1]);
 if(!nf_pc_sky_motion_sample(sky,*alpha,NFPC_SKY_EXACT_ENDPOINTS,lower,sizeof(lower),upper,sizeof(upper),&weight,&destination))goto done;
 unsigned q=(unsigned)floor(weight*65536.+.5);for(unsigned i=0;i<15136;i++){unsigned cell=10560+i,y=cell/240;if(y<top||y>=bottom||!p->background[cell*4+3])continue;const unsigned char*ca=p->base->palette+(y*256+lower[i])*4,*cb=p->base->palette+(y*256+upper[i])*4;for(unsigned c=0;c<3;c++)p->background[cell*4+c]=(unsigned char)((ca[c]*(65536u-q)+cb[c]*q+32768u)/65536u);}
 ok=1;
done:nf_pc_sky_motion_free(sky);return ok;
}
NFPCSceneSample* nf_pc_scene_sample_prepare(NFPCScene*a,NFPCScene*b,double target,unsigned mode,size_t maximum,unsigned*reason){
 if(!a||!b||!isfinite(target)||mode>2){why(reason,NFPC_SAMPLE_ARGUMENT);return NULL;}if(maximum<sizeof(NFPCSceneSample)||maximum>64u*1024*1024){why(reason,NFPC_SAMPLE_BUDGET);return NULL;}
 NFPCSceneRegionPair*pair=nf_pc_scene_region_pair_prepare(a,b,256u*1024);if(!pair){why(reason,NFPC_SAMPLE_PAIR);return NULL;}NFPCSceneSample*p=calloc(1,sizeof(*p));if(!p){nf_pc_scene_region_pair_free(pair);why(reason,NFPC_SAMPLE_BUDGET);return NULL;}p->base=mode==NFPC_SAMPLE_NEWER?b:a;p->target=target;p->info[0]=p->base->info[0];p->info[1]=mode;p->info[12]=sizeof(*p);memcpy(p->background,p->base->background,sizeof(p->background));unsigned failure=NFPC_SAMPLE_SOURCE;
 if(mode!=NFPC_SAMPLE_INTERIOR){p->info[2]=1;p->bands[0][1]=160;p->bands[0][2]=p->bands[0][3]=p->bands[0][4]=UINT32_MAX;p->bands[0][6]=p->base->info[3];p->fractions[0][0]=p->fractions[0][1]=mode==NFPC_SAMPLE_NEWER;
  for(unsigned j=0;j<p->base->info[3];j++){NFPCSceneSampleDraw*d=p->draws+p->info[3]++;d->command=p->base->commands[j];d->trace[0]=j;}
  nf_pc_scene_region_pair_free(pair);why(reason,NFPC_SAMPLE_OK);return p;
 }
 double lo,hi;if(!interval(a,b,pair,&lo,&hi,&failure)||target<lo||target>=hi){if(failure==NFPC_SAMPLE_OK)failure=NFPC_SAMPLE_TIME;goto fail;}
 uint64_t pi[16];if(!nf_pc_scene_region_pair_info(pair,pi))goto fail;p->info[2]=pi[6];p->info[15]=31;
 for(unsigned band=0;band<pi[6];band++){
  uint64_t v[9];if(!nf_pc_scene_region_pair_band(pair,band,v))goto fail;uint64_t*stats=p->bands[band];stats[0]=v[0];stats[1]=v[1];stats[2]=v[2];stats[3]=v[3];stats[4]=v[6];stats[5]=p->info[3];double alpha=0;NFPCWorldMotionOwner*world=NULL;
  if(v[6]==NFPC_REGION_FORWARD){
   if(!nf_pc_scene_pose_alpha(a,(unsigned)v[2],b,(unsigned)v[3],target,&alpha)||alpha>=1||!sky_band(p,b,(unsigned)v[2],(unsigned)v[3],(unsigned)v[0],(unsigned)v[1],target,&p->fractions[band][1]))goto fail;
   p->fractions[band][0]=alpha;p->info[13]++;p->info[6]++;stats[11]=1;if(alpha>0)world=nf_pc_scene_world_pose_owner(a,(unsigned)v[2],b,(unsigned)v[3],alpha,64u*1024*1024);
  }else p->info[14]++;
  uint64_t mapping[288][8];unsigned char found[288]={0};
  for(unsigned r=0;r<v[5];r++){uint64_t row[8];uint32_t id[5];if(!nf_pc_scene_region_pair_row(pair,(unsigned)v[4]+r,row,id)){nf_pc_world_motion_owner_free(world);goto fail;}if(row[1]==UINT32_MAX){p->info[10]++;continue;}if(row[1]>=a->info[3]||found[row[1]]){nf_pc_world_motion_owner_free(world);goto fail;}found[row[1]]=1;memcpy(mapping[row[1]],row,sizeof(row));}
  for(unsigned j=0;j<a->info[3];j++)if(a->commands[j].info[0]==v[2]){
   if(!found[j]||p->info[3]>=864){nf_pc_world_motion_owner_free(world);goto fail;}NFPCSceneSampleDraw*d=p->draws+p->info[3]++;d->command=a->commands[j];d->command.info[13]=v[0];d->command.info[14]=v[1];d->trace[0]=j;d->trace[1]=band;d->trace[2]=mapping[j][0];
   if(mapping[j][0]==NFPC_PAIR_OLDER_ONLY){d->trace[4]|=2;p->info[9]++;}
   if(v[6]==NFPC_REGION_FORWARD&&alpha>0){
    size_t remaining=maximum-p->info[12],cap=remaining<32u*1024*1024?remaining:32u*1024*1024;uint64_t original[16];
    if(d->command.info[1]){if(mapping[j][0]==NFPC_PAIR_SHARED&&mapping[j][2]!=UINT32_MAX){if(!nf_pc_model_mesh_info(d->command.model,original)||original[6]>cap){failure=NFPC_SAMPLE_BUDGET;nf_pc_world_motion_owner_free(world);goto fail;}d->model=nf_pc_scene_model_pose(a,j,b,(unsigned)mapping[j][2],alpha,cap);}}
    else if(world){if(!nf_pc_world_mesh_info(d->command.world,original)||original[15]>cap){failure=NFPC_SAMPLE_BUDGET;nf_pc_world_motion_owner_free(world);goto fail;}d->world=nf_pc_world_motion_owner_class_mesh(world,(unsigned)d->command.info[2],cap);}
    if(d->model||d->world){if(!sampled_planes(p,d,maximum)){failure=NFPC_SAMPLE_BUDGET;nf_pc_world_motion_owner_free(world);goto fail;}d->trace[3]=d->model?1:2;p->info[d->model?4:5]++;stats[d->model?7:8]++;}
    else{d->trace[4]|=1;p->info[8]++;stats[10]++;}
   }
   if(!d->trace[3]){p->info[7]++;stats[9]++;}stats[6]++;
  }
  nf_pc_world_motion_owner_free(world);
 }
 nf_pc_scene_region_pair_free(pair);why(reason,NFPC_SAMPLE_OK);return p;
fail:nf_pc_scene_region_pair_free(pair);nf_pc_scene_sample_free(p);why(reason,failure);return NULL;
}
void nf_pc_scene_sample_free(NFPCSceneSample*p){if(!p)return;for(unsigned i=0;i<p->info[3];i++){nf_pc_model_mesh_free(p->draws[i].model);nf_pc_world_mesh_free(p->draws[i].world);free(p->draws[i].planes);}free(p);}
int nf_pc_scene_sample_info(const NFPCSceneSample*p,uint64_t out[16],double*target){if(!p||!out||!target)return 0;memcpy(out,p->info,sizeof(p->info));*target=p->target;return 1;}
int nf_pc_scene_sample_band(const NFPCSceneSample*p,unsigned i,uint64_t out[12],double fractions[2]){if(!p||i>=p->info[2]||!out||!fractions)return 0;memcpy(out,p->bands[i],sizeof(p->bands[i]));memcpy(fractions,p->fractions[i],sizeof(p->fractions[i]));return 1;}
int nf_pc_scene_sample_command(const NFPCSceneSample*p,unsigned i,uint64_t out[5]){if(!p||i>=p->info[3]||!out)return 0;memcpy(out,p->draws[i].trace,sizeof(p->draws[i].trace));return 1;}
