#include "world_material.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
struct NFPCWorldMaterial{uint64_t info[8];size_t pixels;unsigned char*source,*rgba;int cached;double curve[6];};
static double number(const void*p,size_t at){double v;memcpy(&v,(const unsigned char*)p+at,8);return v;}
static uint32_t word(const void*p,size_t at){uint32_t v;memcpy(&v,(const unsigned char*)p+at,4);return v;}
static int curve(const NFPCWorld*w,unsigned i,const void*light,NFPCWorldMaterial*m){NFPCWorldMesh*mesh=nf_pc_world_mesh(w,i,32u*1024*1024);if(!mesh)return 0;uint64_t meta[16];const void*points,*model;size_t n,mn;int ok=0;if(!nf_pc_world_mesh_info(mesh,meta)||!nf_pc_world_mesh_buffer(mesh,1,&points,&n)||n<48||!nf_pc_world_model(w,0,&model,&mn)||mn<160)goto done;
 double x[2]={number(points,0),number(points,24)},z[2]={number(points,16),number(points,40)},shade[2]={word(light,4),word(light,8)},center=number(model,24),scale=number(model,40);
 if(!isfinite(center)||!isfinite(scale)||scale<=0)goto done;
 for(unsigned k=0;k<2;k++)if(!isfinite(x[k])||!isfinite(z[k])||!isfinite(shade[k])||shade[k]<0||shade[k]>15)goto done;
 if(z[0]<64&&z[1]<64){ok=meta[12]==0;goto done;}
 for(unsigned k=0;k<2;k++)if(z[k]<64){unsigned other=1-k;double t=(64-z[k])/(z[other]-z[k]);x[k]+=(x[other]-x[k])*t;shade[k]+=(shade[other]-shade[k])*t;z[k]=64;}
 for(unsigned k=0;k<2;k++){x[k]=center+scale*x[k]/z[k];if(!isfinite(x[k])||x[k]< -32760||x[k]>32760||z[k]>32767)goto done;}
 m->curve[0]=x[0];m->curve[1]=x[1];m->curve[2]=z[0];m->curve[3]=z[1];m->curve[4]=shade[0];m->curve[5]=shade[1];m->info[6]=1;ok=1;
done:nf_pc_world_mesh_free(mesh);return ok;}
NFPCWorldMaterial* nf_pc_world_material(const NFPCWorld*w,unsigned i,size_t maximum){uint64_t meta[12];const void*rgba,*states,*indices,*lighting;size_t rn,sn,in,ln;if(!nf_pc_world_surface_info(w,i,meta)||!nf_pc_world_surface_buffer(w,i,2,&rgba,&rn)||!nf_pc_world_surface_buffer(w,i,4,&lighting,&ln)||!nf_pc_world_surface_buffer(w,i,5,&states,&sn)||!nf_pc_world_surface_buffer(w,i,6,&indices,&in))return NULL;
 unsigned mode=(unsigned)meta[4],lit=(unsigned)meta[5],indexed=in!=0;size_t pixels=(size_t)meta[1]*meta[2];if(rn!=pixels*4||maximum>64u*1024*1024)return NULL;
 for(size_t p=3;p<rn;p+=4)if(((const unsigned char*)rgba)[p]!=0&&((const unsigned char*)rgba)[p]!=255)return NULL;
 if(lit){if(meta[3]!=2||meta[0]!=4||(mode!=3&&mode!=8)||sn!=17*pixels||ln!=20+64*pixels||(indexed&&in!=17*pixels))return NULL;}
 else if(mode!=0&&mode!=1&&mode!=2&&mode!=4&&mode!=5&&mode!=6&&mode!=7&&mode!=9&&mode!=10)return NULL;
 if(!lit&&((sn&&sn!=pixels)||(in&&in!=pixels)))return NULL;
 size_t source_bytes=lit?17*pixels+(indexed?17*pixels:64*pixels):0,used=sizeof(NFPCWorldMaterial)+source_bytes+pixels*4;if(used>maximum)return NULL;
 NFPCWorldMaterial*m=calloc(1,sizeof(*m));if(!m)return NULL;m->pixels=pixels;m->info[0]=meta[1];m->info[1]=meta[2];m->info[2]=meta[3];m->info[3]=mode;m->info[4]=indexed;m->info[5]=lit;m->info[7]=used;m->cached=-1;
 m->rgba=malloc(pixels*4);if(source_bytes)m->source=malloc(source_bytes);if(!m->rgba||(source_bytes&&!m->source))goto fail;
 if(lit){if(!curve(w,i,lighting,m))goto fail;memcpy(m->source,states,17*pixels);memcpy(m->source+17*pixels,indexed?indices:(const unsigned char*)lighting+20,indexed?17*pixels:64*pixels);
 for(unsigned level=0;level<16;level++)for(size_t p=0;p<pixels;p++){unsigned state=m->source[(level+1)*pixels+p];if(state>2||(indexed&&((state==2)!=(m->source[17*pixels+(level+1)*pixels+p]!=0))))goto fail;}}
 else{for(size_t p=0;p<pixels;p++){unsigned state=sn?((const unsigned char*)states)[p]:2;if(state!=0&&state!=2)goto fail;if(indexed){m->rgba[p*4]=((const unsigned char*)indices)[p];m->rgba[p*4+1]=m->rgba[p*4+2]=0;}else memcpy(m->rgba+p*4,(const unsigned char*)rgba+p*4,3);m->rgba[p*4+3]=(unsigned char)(state==0?0:255);}
 if(!sn&&!indexed){memcpy(m->rgba,rgba,rn);}m->cached=0;}
 const void*image;size_t size;if(!nf_pc_world_material_image(m,0,&image,&size))goto fail;return m;
fail:nf_pc_world_material_free(m);return NULL;}
void nf_pc_world_material_free(NFPCWorldMaterial*m){if(m){free(m->source);free(m->rgba);free(m);}}
int nf_pc_world_material_info(const NFPCWorldMaterial*m,uint64_t out[8]){if(!m||!out)return 0;memcpy(out,m->info,sizeof(m->info));return 1;}
int nf_pc_world_material_image(NFPCWorldMaterial*m,unsigned level,const void**p,size_t*n){if(!m||!p||!n||level>=16||(!m->info[5]&&level))return 0;if(m->info[5]&&m->cached!=(int)level){for(size_t pixel=0;pixel<m->pixels;pixel++){unsigned state=m->source[(level+1)*m->pixels+pixel];if(m->info[4]){m->rgba[pixel*4]=m->source[17*m->pixels+(level+1)*m->pixels+pixel];m->rgba[pixel*4+1]=m->rgba[pixel*4+2]=0;}else memcpy(m->rgba+pixel*4,m->source+17*m->pixels+(level*m->pixels+pixel)*4,3);m->rgba[pixel*4+3]=(unsigned char)(state==0?0:state==1?128:255);}m->cached=(int)level;}*p=m->rgba;*n=m->pixels*4;return 1;}
int nf_pc_world_material_curve(const NFPCWorldMaterial*m,double out[6]){if(!m||!out||!m->info[6])return 0;memcpy(out,m->curve,sizeof(m->curve));return 1;}
int nf_pc_world_material_columns(const NFPCWorldMaterial*m,unsigned count,uint32_t*out,size_t bytes){if(!m||!m->info[6]||!out||!count||count>16384||bytes<(size_t)count*4)return 0;double x0=m->curve[0],x1=m->curve[1],z0=m->curve[2],z1=m->curve[3],s0=m->curve[4],s1=m->curve[5];for(unsigned i=0;i<count;i++){double value;if(s0==s1)value=s0;else{double p=(i+.5)*240/count,t=x1==x0?.5:(p-x0)/(x1-x0);if(t<0)t=0;if(t>1)t=1;double a=(1-t)/z0,b=t/z1;value=(a*s0+b*s1)/(a+b);}int level=(int)floor(value+1e-10);out[i]=(uint32_t)(level<0?0:level>15?15:level);}return 1;}

