#include "scene_region_pair.h"
#include <stdlib.h>
#include <string.h>
typedef struct{uint64_t meta[16],owner[5];uint32_t id[5];} Command;
typedef struct{uint64_t info[8];uint32_t id[5];} Row;
struct NFPCSceneRegionPair{uint64_t info[16],bands[3][9],owners[3][2][5];Row rows[];};
static unsigned matches(const Command*commands,const unsigned*indices,unsigned count,const uint32_t id[5],unsigned*target){unsigned found=0;for(unsigned j=0;j<count;j++)if(!memcmp(commands[indices[j]].id,id,20)){found++;if(target)*target=indices[j];}return found;}
static void append(NFPCSceneRegionPair*p,unsigned band,const Command*a,unsigned ai,const Command*b,unsigned bi,unsigned status){
 Row*r=p->rows+p->info[5]++;const Command*c=a?a:b;uint64_t flags=p->bands[band][6]==NFPC_REGION_DISCONTINUITY?NFPC_PAIR_TEMPORAL_BREAK:0;
 if(a&&b){static const unsigned fields[]={3,4,6,7,8,9,10,11,12,13,14};for(unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);i++)if(a->meta[fields[i]]!=b->meta[fields[i]])flags|=NFPC_PAIR_METADATA_CHANGED;if(a->meta[15]!=b->meta[15])flags|=NFPC_PAIR_ORDER_CHANGED;}
 uint64_t v[8]={status,ai,bi,band,flags,a?a->meta[15]:UINT32_MAX,b?b->meta[15]:UINT32_MAX,c->id[0]};memcpy(r->info,v,sizeof(v));memcpy(r->id,c->id,20);
 p->info[status==NFPC_PAIR_SHARED?7:status==NFPC_PAIR_HELD_OWNER?8:status==NFPC_PAIR_OLDER_ONLY?9:status==NFPC_PAIR_NEWER_ONLY?10:status==NFPC_PAIR_AMBIGUOUS?11:12]++;
}
NFPCSceneRegionPair* nf_pc_scene_region_pair_prepare(const NFPCScene*a,const NFPCScene*b,size_t maximum){
 uint64_t info[2][8];if(!nf_pc_scene_info(a,info[0])||!nf_pc_scene_info(b,info[1])||!info[0][0]||info[0][0]!=info[1][0]||info[1][1]<=info[0][1]||info[1][1]-info[0][1]>8)return NULL;
 for(unsigned ep=0;ep<2;ep++)if(info[ep][2]<1||info[ep][2]>2||info[ep][3]>288||info[ep][7]>160)return NULL;
 unsigned cuts[4]={0,160,0,160},n=2;for(unsigned ep=0;ep<2;ep++)if(info[ep][2]==2&&info[ep][7]>0&&info[ep][7]<160)cuts[n++]=(unsigned)info[ep][7];
 for(unsigned i=0;i<n;i++)for(unsigned j=i+1;j<n;j++)if(cuts[j]<cuts[i]){unsigned x=cuts[i];cuts[i]=cuts[j];cuts[j]=x;}
 unsigned unique=1;for(unsigned i=1;i<n;i++)if(cuts[i]!=cuts[unique-1])cuts[unique++]=cuts[i];unsigned bands=unique-1;
 size_t bytes=sizeof(NFPCSceneRegionPair)+(size_t)bands*(info[0][3]+info[1][3])*sizeof(Row);if(bytes>maximum||maximum>256u*1024)return NULL;
 NFPCSceneRegionPair*p=calloc(1,bytes);if(!p)return NULL;p->info[0]=info[0][0];p->info[1]=info[0][1];p->info[2]=info[1][1];p->info[3]=info[0][3];p->info[4]=info[1][3];p->info[6]=bands;p->info[13]=bytes;p->info[14]=info[0][2];p->info[15]=info[1][2];
 Command commands[2][288];uint64_t owners[2][2][5]={{{0}}};unsigned seen[2][2]={{0}};const NFPCScene*scenes[]={a,b};
 for(unsigned ep=0;ep<2;ep++)for(unsigned i=0;i<info[ep][3];i++){
  Command*c=commands[ep]+i;if(!nf_pc_scene_command_info(scenes[ep],i,c->meta)||!nf_pc_scene_command_source(scenes[ep],i,c->owner,c->id)||c->meta[0]>=info[ep][2]||c->owner[0]!=p->info[0]||c->owner[2]>c->owner[3]||c->owner[4]>1||!c->id[0])goto fail;
  unsigned role=(unsigned)c->meta[0];if(seen[ep][role]&&memcmp(owners[ep][role],c->owner,40))goto fail;memcpy(owners[ep][role],c->owner,40);seen[ep][role]=1;
 }
 for(unsigned band=0;band<bands;band++){
  uint64_t*r=p->bands[band];r[0]=cuts[band];r[1]=cuts[band+1];unsigned indices[2][288],counts[2]={0};
  for(unsigned ep=0;ep<2;ep++){
   unsigned role=info[ep][2]==1||cuts[band]<info[ep][7]?0:1;if(!seen[ep][role])goto fail;r[2+ep]=role;memcpy(p->owners[band][ep],owners[ep][role],40);
   for(unsigned i=0;i<info[ep][3];i++){if(commands[ep][i].meta[0]==role)indices[ep][counts[ep]++]=i;}
   r[7+ep]=counts[ep];
  }
  const uint64_t*x=p->owners[band][0],*y=p->owners[band][1];unsigned mode=!memcmp(x,y,40)?NFPC_REGION_HELD:y[1]>x[1]&&y[3]>x[3]&&y[3]-x[3]<=8?NFPC_REGION_FORWARD:NFPC_REGION_DISCONTINUITY;r[6]=mode;r[4]=p->info[5];unsigned used[288]={0};
  for(unsigned j=0;j<counts[0];j++){
   unsigned i=indices[0][j],target=0;Command*c=commands[0]+i;unsigned oc=matches(commands[0],indices[0],counts[0],c->id,NULL),nc=matches(commands[1],indices[1],counts[1],c->id,&target);
   if(oc>1||nc>1)append(p,band,c,i,NULL,UINT32_MAX,NFPC_PAIR_AMBIGUOUS);
   else if(nc==1){used[target]=1;append(p,band,c,i,commands[1]+target,target,mode==NFPC_REGION_HELD?NFPC_PAIR_HELD_OWNER:mode==NFPC_REGION_FORWARD?NFPC_PAIR_SHARED:NFPC_PAIR_DISCONTINUITY);}
   else append(p,band,c,i,NULL,UINT32_MAX,NFPC_PAIR_OLDER_ONLY);
  }
  for(unsigned j=0;j<counts[1];j++){unsigned i=indices[1][j];if(!used[i]){Command*c=commands[1]+i;unsigned oc=matches(commands[0],indices[0],counts[0],c->id,NULL),nc=matches(commands[1],indices[1],counts[1],c->id,NULL);append(p,band,NULL,UINT32_MAX,c,i,oc>1||nc>1?NFPC_PAIR_AMBIGUOUS:NFPC_PAIR_NEWER_ONLY);}}
  r[5]=p->info[5]-r[4];
 }
 return p;
fail:free(p);return NULL;
}
void nf_pc_scene_region_pair_free(NFPCSceneRegionPair*p){free(p);}
int nf_pc_scene_region_pair_info(const NFPCSceneRegionPair*p,uint64_t out[16]){if(!p||!out)return 0;memcpy(out,p->info,sizeof(p->info));return 1;}
int nf_pc_scene_region_pair_band(const NFPCSceneRegionPair*p,unsigned i,uint64_t out[9]){if(!p||!out||i>=p->info[6])return 0;memcpy(out,p->bands[i],sizeof(p->bands[i]));return 1;}
int nf_pc_scene_region_pair_row(const NFPCSceneRegionPair*p,unsigned i,uint64_t out[8],uint32_t id[5]){if(!p||!out||!id||i>=p->info[5])return 0;memcpy(out,p->rows[i].info,sizeof(p->rows[i].info));memcpy(id,p->rows[i].id,sizeof(p->rows[i].id));return 1;}
int nf_pc_scene_region_pair_owner(const NFPCSceneRegionPair*p,unsigned i,unsigned ep,uint64_t out[5]){if(!p||!out||i>=p->info[6]||ep>1)return 0;memcpy(out,p->owners[i][ep],40);return 1;}
