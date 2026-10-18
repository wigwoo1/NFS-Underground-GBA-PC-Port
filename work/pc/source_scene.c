#include "empty_model_plane.h"
#include "scene_internal.h"
#include "source_background.h"
#include <stdlib.h>
#include <string.h>
static int sky_part(const unsigned char*p,size_t size,unsigned i,const unsigned char**out,size_t*n){
 if(size<128||i>3)return 0;
 uint64_t at,length;memcpy(&at,p+64+i*16,8);memcpy(&length,p+72+i*16,8);
 if(at>size||length>size-at)return 0;
 *out=p+(size_t)at;*n=(size_t)length;return 1;
}
static int source_sky(const NFPCSourceFrame*f,unsigned owner,const unsigned char**p,size_t*n){
 const void*root;size_t size;const unsigned char*sky;size_t sn;
 return nf_pc_source_frame_component(f,0,NFPC_BACKGROUND,&root,&size)&&sky_part(root,size,0,&sky,&sn)&&sky_part(sky,sn,owner+1,p,n)&&*n==30568;
}
static size_t cap32(size_t n){return n<32u*1024*1024?n:32u*1024*1024;}
static int retain(NFPCScene*s,size_t n,size_t maximum){if(n>maximum-s->info[6])return 0;s->info[6]+=n;return 1;}
static NFPCScene* prepare_scene(const NFPCSourceFrame*frame,size_t maximum,int motion){uint64_t f[8];if(maximum<sizeof(NFPCScene)||maximum>64u*1024*1024||!nf_pc_source_frame_info(frame,f)||f[4]<1||f[4]>2)return NULL;NFPCScene*s=calloc(1,sizeof(*s));if(!s)return NULL;s->info[0]=f[0];s->info[1]=f[1];s->info[2]=f[4];s->info[6]=sizeof(*s);s->info[7]=f[3];
 if(!nf_pc_source_background_rgba(frame,s->background,sizeof(s->background))||!nf_pc_source_palette_rgba(frame,s->palette,sizeof(s->palette)))goto fail;
 s->hud=nf_pc_source_hud(frame,maximum-s->info[6]);uint64_t hi[5];if(!s->hud||!nf_pc_hud_info(s->hud,hi)||hi[0]!=f[0]||hi[1]!=f[1]||!retain(s,(size_t)hi[4],maximum))goto fail;
 for(unsigned owner=0;owner<f[4];owner++){if(!nf_pc_source_frame_owner(frame,owner,s->owner[owner])||s->owner[owner][0]!=f[0])goto fail;
 for(unsigned layer=0;layer<2;layer++){uint64_t ri[10];s->retained[owner][layer]=nf_pc_source_retention(frame,owner,NFPC_ROAD+layer,maximum-s->info[6]);if(!s->retained[owner][layer]||!nf_pc_retention_info(s->retained[owner][layer],ri)||memcmp(ri,s->owner[owner],5*sizeof(uint64_t))||!retain(s,(size_t)ri[9],maximum))goto fail;
 const void*records;size_t rn;if(!nf_pc_retention_buffer(s->retained[owner][layer],1,&records,&rn)||rn!=ri[8]*16)goto fail;size_t bytes=(size_t)ri[8]*6*4*sizeof(float);s->retention_vertex_bytes[owner][layer]=bytes;if(bytes){if(!retain(s,bytes,maximum)||(s->retention_vertices[owner][layer]=malloc(bytes))==NULL)goto fail;static const unsigned corner[12]={0,0,1,0,0,1,0,1,1,0,1,1};float*v=s->retention_vertices[owner][layer];const uint32_t*r=records;for(size_t cell=0;cell<ri[8];cell++){unsigned x=r[cell*4]%240,y=r[cell*4]/240;float u=((float)x+.5f)/240.0f,t=((float)y+.5f)/160.0f;for(unsigned j=0;j<6;j++){size_t at=(cell*6+j)*4;v[at]=(float)(x+corner[j*2]);v[at+1]=(float)(y+corner[j*2+1]);v[at+2]=u;v[at+3]=t;}}}
 }
 NFPCWorld*w=nf_pc_source_world(frame,owner,64u*1024*1024);if(!w)goto fail;uint64_t wi[4];int valid=0;if(!nf_pc_world_info(w,wi))goto owner_done;
 for(unsigned order=0;order<wi[2];order++){if(s->info[3]>=288)goto owner_done;uint64_t command[2];if(!nf_pc_world_command(w,order,command))goto owner_done;NFPCSceneCommand*c=&s->commands[s->info[3]++];uint64_t*m=c->info;m[0]=owner;m[1]=command[0];m[2]=command[1];m[13]=owner==0?0:f[3];m[14]=f[4]==1||owner==1?160:f[3];m[15]=order;
 if(command[0]){if(!nf_pc_world_model_identity(w,(unsigned)command[1],c->source_identity))goto owner_done;}else{const void*identity;size_t bytes;if(!nf_pc_world_surface_buffer(w,(unsigned)command[1],9,&identity,&bytes)||bytes!=sizeof(c->source_identity))goto owner_done;memcpy(c->source_identity,identity,bytes);}

 if(command[0]){uint64_t model[12];c->model=nf_pc_source_model_mesh(frame,owner,(unsigned)command[1],cap32(maximum-s->info[6]));if(!c->model||!nf_pc_model_mesh_info(c->model,model)||!retain(s,model[6],maximum)||model[11]!=order)goto owner_done;m[3]=model[0];m[4]=model[1];m[5]=model[4];m[6]=model[5];for(unsigned j=0;j<4;j++)m[9+j]=model[7+j];const void*indices;size_t n;if(!nf_pc_model_mesh_buffer(c->model,0,&c->vertices,&c->vertices_bytes)||!nf_pc_model_mesh_buffer(c->model,2,&c->image,&n)||!nf_pc_model_mesh_buffer(c->model,3,&indices,&n))goto owner_done;
 if(model[5]){size_t pixels=model[0]*model[1];if(n!=pixels||!retain(s,pixels*4,maximum)||(c->owned_image=malloc(pixels*4))==NULL)goto owner_done;for(size_t i=0;i<pixels;i++){c->owned_image[i*4]=((const unsigned char*)indices)[i];c->owned_image[i*4+1]=c->owned_image[i*4+2]=0;c->owned_image[i*4+3]=255;}c->image=c->owned_image;}s->info[4]++;}
 else{uint64_t world[16],material[8];c->world=nf_pc_world_mesh(w,(unsigned)command[1],cap32(maximum-s->info[6]));if(!c->world||!nf_pc_world_mesh_info(c->world,world)||!retain(s,world[15],maximum)||world[11]!=order)goto owner_done;c->material=nf_pc_world_material(w,(unsigned)command[1],maximum-s->info[6]);if(!c->material||!nf_pc_world_material_info(c->material,material)||!retain(s,material[7],maximum))goto owner_done;m[3]=world[1];m[4]=world[2];m[5]=world[12];m[6]=material[4];m[7]=world[3]==2;m[8]=material[5];for(unsigned j=0;j<4;j++)m[9+j]=world[7+j];if(!nf_pc_world_mesh_buffer(c->world,0,&c->vertices,&c->vertices_bytes))goto owner_done;s->info[5]++;}
 size_t plane_bytes=(size_t)m[5]/3*11*sizeof(float);if(plane_bytes){if(!retain(s,plane_bytes,maximum)||(c->planes=malloc(plane_bytes))==NULL)goto owner_done;for(unsigned i=0;i<m[5]/3;i++){float*p=c->planes+i*11;if(!(c->model?nf_pc_model_mesh_plane(c->model,i,p):nf_pc_world_mesh_plane(c->world,i,p))&&!(c->model&&nf_pc_empty_model_plane((const float*)c->vertices+i*15,p)))goto owner_done;}}
 const void*image;size_t n;if(!nf_pc_scene_command_image(s,(unsigned)s->info[3]-1,0,&image,&n)||n!=m[3]*m[4]*4||c->vertices_bytes!=m[5]*20)goto owner_done;
 }
 valid=1;
owner_done:if(valid&&motion){if(!retain(s,(size_t)wi[3],maximum))valid=0;else{s->motion_source[owner]=w;w=NULL;const unsigned char*sky;size_t sn;if(!source_sky(frame,owner,&sky,&sn)||!retain(s,sn,maximum)||(s->motion_sky[owner]=malloc(sn))==NULL)valid=0;else memcpy(s->motion_sky[owner],sky,sn);if(valid){const void*timing;size_t tn;if(nf_pc_source_frame_pose_timing(frame,owner,&timing,&tn)){if(tn!=184||!retain(s,tn,maximum)||(s->motion_timing[owner]=malloc(tn))==NULL)valid=0;else memcpy(s->motion_timing[owner],timing,tn);}}}}nf_pc_world_free(w);if(!valid)goto fail;
 }
 return s;
fail:nf_pc_scene_free(s);return NULL;}
void nf_pc_scene_free(NFPCScene*s){if(!s)return;for(unsigned owner=0;owner<2;owner++){nf_pc_world_free(s->motion_source[owner]);free(s->motion_sky[owner]);free(s->motion_timing[owner]);}nf_pc_hud_free(s->hud);for(unsigned owner=0;owner<2;owner++)for(unsigned layer=0;layer<2;layer++){nf_pc_retention_free(s->retained[owner][layer]);free(s->retention_vertices[owner][layer]);}for(unsigned i=0;i<s->info[3];i++){NFPCSceneCommand*c=s->commands+i;nf_pc_model_mesh_free(c->model);nf_pc_world_mesh_free(c->world);nf_pc_world_material_free(c->material);free(c->planes);free(c->owned_image);}free(s);}
int nf_pc_scene_info(const NFPCScene*s,uint64_t out[8]){if(!s||!out)return 0;memcpy(out,s->info,sizeof(s->info));return 1;}
int nf_pc_scene_command_info(const NFPCScene*s,unsigned i,uint64_t out[16]){if(!s||i>=s->info[3]||!out)return 0;memcpy(out,s->commands[i].info,16*sizeof(uint64_t));return 1;}
int nf_pc_scene_buffer(const NFPCScene*s,unsigned kind,const void**p,size_t*n){if(!s||kind>1||!p||!n)return 0;*p=kind?s->palette:s->background;*n=kind?sizeof(s->palette):sizeof(s->background);return 1;}
int nf_pc_scene_command_buffer(const NFPCScene*s,unsigned i,unsigned kind,const void**p,size_t*n){if(!s||i>=s->info[3]||kind>1||!p||!n)return 0;const NFPCSceneCommand*c=s->commands+i;*p=kind?(const void*)c->planes:c->vertices;*n=kind?(size_t)c->info[5]/3*44:c->vertices_bytes;return 1;}
int nf_pc_scene_command_image(NFPCScene*s,unsigned i,unsigned level,const void**p,size_t*n){if(!s||i>=s->info[3]||!p||!n)return 0;NFPCSceneCommand*c=s->commands+i;if(c->material)return nf_pc_world_material_image(c->material,level,p,n);if(level)return 0;*p=c->image;*n=(size_t)c->info[3]*c->info[4]*4;return 1;}
int nf_pc_scene_command_columns(const NFPCScene*s,unsigned i,unsigned width,uint32_t*out,size_t bytes){return s&&i<s->info[3]&&s->commands[i].material?nf_pc_world_material_columns(s->commands[i].material,width,out,bytes):0;}
int nf_pc_scene_retention_info(const NFPCScene*s,unsigned owner,unsigned kind,uint64_t out[10]){return s&&owner<s->info[2]&&(kind==NFPC_ROAD||kind==NFPC_WALL)?nf_pc_retention_info(s->retained[owner][kind-NFPC_ROAD],out):0;}
int nf_pc_scene_retention_buffer(const NFPCScene*s,unsigned owner,unsigned kind,unsigned buffer,const void**p,size_t*n){if(!s||owner>=s->info[2]||(kind!=NFPC_ROAD&&kind!=NFPC_WALL)||!p||!n||buffer>2)return 0;if(buffer==2){*p=s->retention_vertices[owner][kind-NFPC_ROAD];*n=s->retention_vertex_bytes[owner][kind-NFPC_ROAD];return 1;}return nf_pc_retention_buffer(s->retained[owner][kind-NFPC_ROAD],buffer,p,n);}

int nf_pc_scene_hud_info(const NFPCScene*s,uint64_t out[5]){return s?nf_pc_hud_info(s->hud,out):0;}
int nf_pc_scene_hud_buffer(const NFPCScene*s,unsigned kind,const void**p,size_t*n){return s?nf_pc_hud_buffer(s->hud,kind,p,n):0;}

int nf_pc_scene_command_source(const NFPCScene*s,unsigned i,uint64_t owner[5],uint32_t identity[5]){if(!s||i>=s->info[3]||!owner||!identity)return 0;memcpy(owner,s->owner[s->commands[i].info[0]],5*sizeof(uint64_t));memcpy(identity,s->commands[i].source_identity,5*sizeof(uint32_t));return 1;}

NFPCScene* nf_pc_scene_prepare(const NFPCSourceFrame*f,size_t maximum){return prepare_scene(f,maximum,0);}
NFPCScene* nf_pc_scene_prepare_motion(const NFPCSourceFrame*f,size_t maximum){return prepare_scene(f,maximum,1);}
int nf_pc_scene_motion_packet(const NFPCScene*s,unsigned owner,const void**p,size_t*n){return s&&owner<s->info[2]&&s->motion_source[owner]?nf_pc_world_packet(s->motion_source[owner],p,n):0;}
int nf_pc_scene_motion_model(const NFPCScene*s,unsigned i,const void**p,size_t*n){if(!s||i>=s->info[3]||!s->commands[i].info[1])return 0;const NFPCSceneCommand*c=s->commands+i;return s->motion_source[c->info[0]]?nf_pc_world_model(s->motion_source[c->info[0]],(unsigned)c->info[2],p,n):0;}

int nf_pc_scene_motion_sky(const NFPCScene*s,unsigned owner,const void**p,size_t*n){if(!s||owner>=s->info[2]||!s->motion_sky[owner]||!p||!n)return 0;*p=s->motion_sky[owner];*n=30568;return 1;}

int nf_pc_scene_motion_timing(const NFPCScene*s,unsigned owner,const void**p,size_t*n){if(!s||owner>=s->info[2]||!s->motion_timing[owner]||!p||!n)return 0;*p=s->motion_timing[owner];*n=184;return 1;}
