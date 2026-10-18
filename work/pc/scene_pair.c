#include "scene_pair.h"
#include <stdlib.h>
#include <string.h>
typedef struct {uint64_t meta[16],owner[5];uint32_t identity[5];} Command;
typedef struct {uint64_t info[8];uint32_t identity[5];} Row;
struct NFPCScenePair{uint64_t info[16],owner[2][2][5];Row rows[];};
static int same(const Command*a,const Command*b){return a->meta[0]==b->meta[0]&&!memcmp(a->identity,b->identity,sizeof(a->identity));}
static unsigned count(const Command*rows,unsigned n,const Command*key,unsigned*target){unsigned found=0;for(unsigned i=0;i<n;i++)if(same(rows+i,key)){found++;if(target)*target=i;}return found;}
static void append(NFPCScenePair*p,const Command*a,unsigned ai,const Command*b,unsigned bi,unsigned status){
 Row*r=&p->rows[p->info[5]++];const Command*c=a?a:b;uint64_t flags=0;
 if(a&&b){static const unsigned fields[]={3,4,6,7,8,9,10,11,12,13,14};for(unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);i++)if(a->meta[fields[i]]!=b->meta[fields[i]])flags|=NFPC_PAIR_METADATA_CHANGED;
 if(a->meta[15]!=b->meta[15])flags|=NFPC_PAIR_ORDER_CHANGED;}
 uint64_t v[8]={status,ai,bi,c->meta[0],flags,a?a->meta[15]:UINT32_MAX,b?b->meta[15]:UINT32_MAX,c->identity[0]};memcpy(r->info,v,sizeof(v));memcpy(r->identity,c->identity,sizeof(r->identity));
 p->info[status==NFPC_PAIR_SHARED?6:status==NFPC_PAIR_OLDER_ONLY?7:status==NFPC_PAIR_NEWER_ONLY?8:status==NFPC_PAIR_AMBIGUOUS?9:10]++;
 if(flags&NFPC_PAIR_METADATA_CHANGED)p->info[11]++;
 if(flags&NFPC_PAIR_ORDER_CHANGED)p->info[12]++;
}
NFPCScenePair* nf_pc_scene_pair_prepare(const NFPCScene*a,const NFPCScene*b,size_t maximum){
 uint64_t ai[8],bi[8];if(!nf_pc_scene_info(a,ai)||!nf_pc_scene_info(b,bi)||!ai[0]||ai[0]!=bi[0]||bi[1]<=ai[1]||bi[1]-ai[1]>8||ai[2]<1||ai[2]>2||ai[2]!=bi[2]||ai[7]!=bi[7]||ai[3]>288||bi[3]>288)return NULL;
 size_t bytes=sizeof(NFPCScenePair)+(size_t)(ai[3]+bi[3])*sizeof(Row);if(maximum<bytes||maximum>128u*1024)return NULL;
 Command old[288],newer[288];Command*endpoints[]={old,newer};const NFPCScene*scenes[]={a,b};uint64_t*infos[]={ai,bi};unsigned seen[2][2]={{0}},held[2]={0};
 NFPCScenePair*p=calloc(1,bytes);if(!p)return NULL;p->info[0]=ai[0];p->info[1]=ai[1];p->info[2]=bi[1];p->info[3]=ai[3];p->info[4]=bi[3];p->info[13]=bytes;p->info[14]=ai[2];p->info[15]=ai[7];
 for(unsigned ep=0;ep<2;ep++)for(unsigned i=0;i<infos[ep][3];i++){
  Command*c=endpoints[ep]+i;if(!nf_pc_scene_command_info(scenes[ep],i,c->meta)||!nf_pc_scene_command_source(scenes[ep],i,c->owner,c->identity)||c->meta[0]>=ai[2]||c->owner[0]!=ai[0]||c->owner[2]>c->owner[3]||c->owner[4]>1||!c->identity[0])goto fail;
  unsigned role=(unsigned)c->meta[0];if(seen[ep][role]&&memcmp(p->owner[ep][role],c->owner,sizeof(c->owner)))goto fail;memcpy(p->owner[ep][role],c->owner,sizeof(c->owner));seen[ep][role]=1;
 }
 for(unsigned role=0;role<ai[2];role++){
  const uint64_t*x=p->owner[0][role],*y=p->owner[1][role];if(!seen[0][role]||!seen[1][role])goto fail;
  held[role]=!memcmp(x,y,5*sizeof(uint64_t));if(!held[role]&&(y[1]<=x[1]||y[3]<=x[3]||y[3]-x[3]>8))goto fail;
 }
 unsigned used[288]={0};
 for(unsigned i=0;i<ai[3];i++){
  unsigned target=0,oc=count(old,(unsigned)ai[3],old+i,NULL),nc=count(newer,(unsigned)bi[3],old+i,&target);
  if(oc>1||nc>1)append(p,old+i,i,NULL,UINT32_MAX,NFPC_PAIR_AMBIGUOUS);
  else if(nc==1){used[target]=1;append(p,old+i,i,newer+target,target,held[old[i].meta[0]]?NFPC_PAIR_HELD_OWNER:NFPC_PAIR_SHARED);}
  else append(p,old+i,i,NULL,UINT32_MAX,NFPC_PAIR_OLDER_ONLY);
 }
 for(unsigned i=0;i<bi[3];i++)if(!used[i]){unsigned oc=count(old,(unsigned)ai[3],newer+i,NULL),nc=count(newer,(unsigned)bi[3],newer+i,NULL);append(p,NULL,UINT32_MAX,newer+i,i,oc>1||nc>1?NFPC_PAIR_AMBIGUOUS:NFPC_PAIR_NEWER_ONLY);}
 return p;
fail:free(p);return NULL;
}
void nf_pc_scene_pair_free(NFPCScenePair*p){free(p);}
int nf_pc_scene_pair_info(const NFPCScenePair*p,uint64_t out[16]){if(!p||!out)return 0;memcpy(out,p->info,sizeof(p->info));return 1;}
int nf_pc_scene_pair_row(const NFPCScenePair*p,unsigned i,uint64_t out[8],uint32_t identity[5]){if(!p||i>=p->info[5]||!out||!identity)return 0;memcpy(out,p->rows[i].info,sizeof(p->rows[i].info));memcpy(identity,p->rows[i].identity,sizeof(p->rows[i].identity));return 1;}
int nf_pc_scene_pair_owner(const NFPCScenePair*p,unsigned owner,unsigned ep,uint64_t out[5]){if(!p||!out||ep>1||owner>=p->info[14])return 0;memcpy(out,p->owner[ep][owner],5*sizeof(uint64_t));return 1;}
