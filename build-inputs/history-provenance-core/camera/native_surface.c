#include "native_surface.h"
#include <stdlib.h>
#include <string.h>
#include "rigid_motion.h"
int nf_memory_read_matches(NFReadMemory read,void*user,uint32_t address,const void*consumed,size_t bytes,void*scratch,size_t capacity){
 if(!read||!consumed||!scratch||bytes>capacity||(uint64_t)address+bytes>0x100000000ull)return 0;
 return read(user,address,scratch,bytes)&&!memcmp(consumed,scratch,bytes);
}
int nf_model_world_rotation_owned(NFReadMemory read,void*user,const uint8_t object[164],int32_t out[12]){
 if(!read||!object||!out)return 0;uint32_t enabled,address,pose[9],result[12]={0};
 memcpy(&address,object+140,4);
 if(address>UINT32_MAX-356u||!read(user,0x03006768u,&enabled,4)||!enabled||!read(user,address+320,pose,36))return 0;
 for(unsigned i=0;i<9;i++)result[i]=pose[i]<<2;
 memcpy(out,result,48);return 1;
}
typedef struct {const NFNativeSceneCommand*command;NFReadMemory read;void*user;const uint8_t*palette;uint8_t material[48];} NFCommandAssetReader;
static int command_asset_read(void*user,uint32_t address,void*out,size_t bytes){
 NFCommandAssetReader*r=user;const uint8_t*data=NULL;uint32_t base=0;size_t size=0;
 if(address>=0xfffe0000u&&address<0xfffe0100u){data=r->command->state;base=0xfffe0000u;size=256;}
 else if(address>=0xfffe0100u&&address<0xfffe0144u){data=r->command->model;base=0xfffe0100u;size=68;}
 else if(address>=0xfffe0200u&&address<0xfffe0230u){data=r->material;base=0xfffe0200u;size=48;}
 else if(address>=0x05000000u&&address<0x05000200u){data=r->palette;base=0x05000000u;size=512;}
 if(data){if((uint64_t)address+bytes>(uint64_t)base+size)return 0;memcpy(out,data+address-base,bytes);return 1;}
 return r->read(r->user,address,out,bytes);
}
int nf_scene_command_road_indices_owned(const NFNativeSceneCommand*command,NFReadMemory read,void*user,uint8_t**out,uint32_t*width,uint32_t*height){
 if(!command||command->kind!=1||command->xyz[2]>1||!read||!out||!width||!height)return 0;
 NFCommandAssetReader owned={0};owned.command=command;owned.read=read;owned.user=user;
 return nf_road_texture_indices_layer_owned(command_asset_read,&owned,0xfffe0000u,command->source,command->xyz[2],out,width,height);
}
static void command_wall_material(NFCommandAssetReader*owned){
 const NFNativeSceneCommand*c=owned->command;uint16_t shift=(uint16_t)c->material[2],height=(uint16_t)c->material[3];
 memcpy(owned->material+8,c->state+80,4);memcpy(owned->material+36,&shift,2);memcpy(owned->material+38,&height,2);memcpy(owned->material+40,c->material+1,4);
}
int nf_scene_command_wall_states_owned(const NFNativeSceneCommand*command,NFReadMemory read,void*user,uint8_t**out,uint32_t*width,uint32_t*height,uint32_t*planes){
 if(!command||command->kind!=2||!read||command->material[2]>10||!command->material[3]||command->material[3]>1024)return 0;
 NFCommandAssetReader owned={0};owned.command=command;owned.read=read;owned.user=user;command_wall_material(&owned);
 return nf_wall_write_states_owned(command_asset_read,&owned,0xfffe0200u,command->xyz[0],out,width,height,planes);
}
int nf_scene_command_wall_indices_owned(const NFNativeSceneCommand*command,NFReadMemory read,void*user,uint8_t**out,uint32_t*width,uint32_t*height,uint32_t*planes){
 if(!command||command->kind!=2||!read||command->material[2]>10||!command->material[3]||command->material[3]>1024)return 0;
 NFCommandAssetReader owned={0};owned.command=command;owned.read=read;owned.user=user;command_wall_material(&owned);
 return nf_wall_output_indices_owned(command_asset_read,&owned,0xfffe0200u,command->xyz[0],out,width,height,planes);
}
int nf_extract_scene_command(const NFNativeSceneCommand*command,NFReadMemory read,void*user,const uint8_t palette[512],const int32_t rotation[12],void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=1;
 if(!command||!read||!palette||!out||!out_size)return 0;
 NFCommandAssetReader owned={0};owned.command=command;owned.read=read;owned.user=user;owned.palette=palette;void*asset=NULL;size_t size=0;int ok=0;
 if(stage)*stage=2;
 if(command->kind==1&&command->xyz[2]<=1)ok=nf_extract_road_candidate_layer(command_asset_read,&owned,0xfffe0000u,command->source,palette,1,command->xyz[2],&asset,&size);
 else if(command->kind==2)ok=nf_extract_wall_candidate_diagnostic(command_asset_read,&owned,0xfffe0000u,command->source,palette,1,&asset,&size,stage);
 else if(command->kind==5&&rotation){uint32_t camera;memcpy(&camera,command->state+84,4);ok=nf_extract_model(command_asset_read,&owned,0xfffe0100u,camera,command->source,rotation,&asset,&size);}
 if(!ok)return 0;
 *out=asset;*out_size=size;if(stage)*stage=0;return 1;
}
int nf_extract_scene_command_full(const NFNativeSceneCommand*command,NFReadMemory read,void*user,const uint8_t palette[512],const int32_t rotation[12],void**out,size_t*out_size,void**out_light,size_t*out_light_size,unsigned*stage){
 if(stage)*stage=1;
 if(!command||!read||!palette||!out||!out_size||!out_light||!out_light_size)return 0;
 void*asset=NULL,*light=NULL;size_t size=0,light_size=0;
 if(command->kind!=2){if(!nf_extract_scene_command(command,read,user,palette,rotation,&asset,&size,stage))return 0;}
 else{
  NFCommandAssetReader owned={0};owned.command=command;owned.read=read;owned.user=user;owned.palette=palette;
  uint32_t owner;command_wall_material(&owned);
  if(stage)*stage=2;
  /* The native plan owns the original region record. Frontend descriptor
     tables need not contain 512 independent regions; scanning that range can
     invent overlapping owners from unrelated ROM data. Use the consumed
     region identity, then let wall extraction validate source containment. */
  uint32_t descriptor_base;uint16_t region;
  memcpy(&descriptor_base,command->state+20,4);memcpy(&region,command->record,2);
  uint64_t descriptor=(uint64_t)descriptor_base+(uint64_t)region*48;
  if(region>=512||descriptor>UINT32_MAX-47u)return 0;owner=(uint32_t)descriptor;
  if(stage)*stage=8;
  if(!nf_extract_wall(command_asset_read,&owned,0xfffe0000u,owner,command->source,0xfffe0200u,command->material[0],command->xyz[0],&asset,&size,&light,&light_size))return 0;
 }
 *out=asset;*out_size=size;*out_light=light;*out_light_size=light_size;if(stage)*stage=0;return 1;
}
static uint16_t h(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static int16_t sh(const uint8_t*p){return (int16_t)h(p);}
static uint32_t w(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static int32_t sw(const uint8_t*p){return (int32_t)w(p);}
static int wall_planes_owned(NFReadMemory read,void*user,uint32_t material_address,unsigned flags,uint8_t**out,uint32_t*out_width,uint32_t*out_height,uint32_t*out_planes,int output_indices){
 if(!read||!out||!out_width||!out_height||!out_planes||(flags&128))return 0;
 uint8_t material[48],context[24],table[4096];
 if(!read(user,material_address,material,sizeof(material)))return 0;
 unsigned shift=h(material+36),height=h(material+38),lit=!(flags&256);
 if(shift>10||!height||height>1024)return 0;
 unsigned width=1u<<shift,planes=lit?17:1;size_t pixels=(size_t)width*height;
 uint32_t address=w(material+40);if((uint64_t)address+pixels>UINT32_MAX)return 0;
 if(lit&&(!read(user,w(material+8),context,sizeof(context))||!read(user,w(context+20),table,sizeof(table))))return 0;
 uint8_t*indices=malloc(pixels),*states=malloc(pixels*planes);
 if(!indices||!states){free(indices);free(states);return 0;}
 if(!read(user,address,indices,pixels)){free(indices);free(states);return 0;}
 for(size_t i=0;i<pixels;i++)states[i]=output_indices?indices[i]:(indices[i]?2:0);
 if(lit)for(unsigned level=0;level<16;level++)for(size_t i=0;i<pixels;i++){
  unsigned index=indices[i],mapped=index?table[index*16+level]:0;states[(level+1)*pixels+i]=output_indices?mapped:(index?(mapped?2:1):0);
 }
 free(indices);*out=states;*out_width=width;*out_height=height;*out_planes=planes;return 1;
}
int nf_wall_write_states_owned(NFReadMemory read,void*user,uint32_t material,unsigned flags,uint8_t**out,uint32_t*w,uint32_t*h,uint32_t*n){return wall_planes_owned(read,user,material,flags,out,w,h,n,0);}
int nf_wall_output_indices_owned(NFReadMemory read,void*user,uint32_t material,unsigned flags,uint8_t**out,uint32_t*w,uint32_t*h,uint32_t*n){return wall_planes_owned(read,user,material,flags,out,w,h,n,1);}
static int indexed_read(NFReadMemory read,void*ctx,uint32_t base,unsigned index,unsigned stride,void*out,size_t size){
 uint64_t address=(uint64_t)base+(uint64_t)index*stride;if(address>UINT32_MAX)return 0;return read(ctx,(uint32_t)address,out,size);
}
static void number(uint8_t*p,double value){memcpy(p,&value,8);}
void nf_surface_free(void*p){free(p);}
int nf_wall_visibility_flag(NFReadMemory read,void*ctx,const uint8_t state[256],const uint8_t source[68],int*visible){
 if(!read||!state||!source||!visible)return 0;
 unsigned hidden=h(source+46)&1,index=h(source+42);uint8_t material[32];
 if(index!=65535){if(!indexed_read(read,ctx,w(state+24),index,32,material,32))return 0;hidden=h(material+14)&1;}
 *visible=!hidden;return 1;
}
static int candidate_palette_policy(const uint8_t*indices,size_t pixels,const uint8_t*palettes,unsigned count,uint8_t out[512],unsigned first){
 if(!indices||!pixels||pixels>1024*1024||!palettes||!count||count>256||!out)return 0;
 uint8_t used[256]={0};for(size_t i=0;i<pixels;i++)used[indices[i]]=1;
 for(unsigned p=1;p<count;p++)for(unsigned i=first;i<256;i++)if(used[i]&&memcmp(palettes+i*2,palettes+p*512+i*2,2))return 0;
 memmove(out,palettes,512);return 1;
}
int nf_candidate_palette(const uint8_t*i,size_t n,const uint8_t*p,unsigned count,uint8_t out[512]){return candidate_palette_policy(i,n,p,count,out,0);}
int nf_wall_candidate_palette(const uint8_t*i,size_t n,const uint8_t*p,unsigned count,uint8_t out[512]){return candidate_palette_policy(i,n,p,count,out,1);}
int nf_model_display_palette(const uint8_t*i,size_t n,const uint8_t*p,unsigned count,uint8_t out[512]){return candidate_palette_policy(i,n,p,count,out,1);}
int nf_wall_owner(NFReadMemory read,void*ctx,uint32_t state_address,uint32_t source,uint32_t*out){
 uint8_t state[256],table[512*48];
 if(!read||!out||state_address>UINT32_MAX-255||!read(ctx,state_address,state,sizeof(state)))return 0;
 uint32_t base=w(state+20),vertices=w(state+16);
 if(base>UINT32_MAX-(sizeof(table)-1)||!read(ctx,base,table,sizeof(table)))return 0;
 unsigned matches=0;uint32_t result=0;
 for(unsigned i=0;i<512;i++){
  const uint8_t*d=table+i*48;unsigned count=h(d+2);uint64_t start=(uint64_t)vertices+h(d)*68ull,end=start+count*68ull;
  if(!count||count>32||end>0x100000000ull)continue;
  if(source>=start&&(uint64_t)source+68<=end&&(source-start)%68==0){if(++matches>1)return 0;result=base+i*48;}
 }
 if(matches!=1)return 0;
 *out=result;return 1;
}
typedef struct {NFReadMemory read;void*ctx;uint8_t material[48],palette[512];} CandidateReader;
static int candidate_read(void*context,uint32_t address,void*out,size_t size){
 CandidateReader*c=context;
 if(address==0xffff0000u&&size==48){memcpy(out,c->material,48);return 1;}
 if(address==0x05000000u&&size==512){memcpy(out,c->palette,512);return 1;}
 return c->read(c->ctx,address,out,size);
}
int nf_extract_wall_candidate_diagnostic(NFReadMemory read,void*ctx,uint32_t state_address,uint32_t source_address,const uint8_t*palettes,unsigned count,void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=1;
 uint8_t state[256],source[68],material[32],animation[8];uint32_t owner;
 if(!read||!out||!out_size||!palettes||!count||count>256||!nf_wall_owner(read,ctx,state_address,source_address,&owner)||
    !read(ctx,state_address,state,256)||!read(ctx,source_address,source,68))return 0;
 if(stage)*stage=2;
 unsigned flags=h(source+46);int visible;
 if(!(flags&256)||(flags&128)||!nf_wall_visibility_flag(read,ctx,state,source,&visible)||!visible)return 0;
 if(stage)*stage=3;
 if(!indexed_read(read,ctx,w(state+32),h(source+44),32,material,32)||!h(material)||
    !indexed_read(read,ctx,w(state+72),h(material),8,animation,8))return 0;
 if(stage)*stage=4;
 uint64_t resolved=(uint64_t)w(state+32)+((unsigned)h(source+44)+h(animation+2))*32ull;
 if(resolved>UINT32_MAX||!read(ctx,(uint32_t)resolved,material,32))return 0;
 if(stage)*stage=5;
 unsigned shift=h(material+26),height=h(material+10);if(shift>10||!height||height>1024)return 0;
 uint32_t texture=w(state)+w(material+4);size_t pixels=(size_t)(1u<<shift)*height;uint8_t*indices=malloc(pixels);if(!indices)return 0;
 CandidateReader c={0};c.read=read;c.ctx=ctx;
 if(stage)*stage=6;
 int ok=read(ctx,texture,indices,pixels);
 if(ok){if(stage)*stage=7;ok=nf_wall_candidate_palette(indices,pixels,palettes,count,c.palette);}
 free(indices);if(!ok)return 0;
 uint16_t sh16=(uint16_t)shift,ht16=(uint16_t)height;memcpy(c.material+36,&sh16,2);memcpy(c.material+38,&ht16,2);memcpy(c.material+40,&texture,4);
 void*surface=NULL,*light=NULL;size_t size=0,light_size=0;
 if(stage)*stage=8;
 ok=nf_extract_wall(candidate_read,&c,state_address,owner,source_address,0xffff0000u,(uint32_t)resolved,flags,&surface,&size,&light,&light_size);
 free(light);if(!ok)return 0;
 if(stage)*stage=0;
 *out=surface;*out_size=size;return 1;
}
int nf_extract_wall_candidate(NFReadMemory read,void*ctx,uint32_t state,uint32_t source,const uint8_t*palettes,unsigned count,void**out,size_t*size){
 return nf_extract_wall_candidate_diagnostic(read,ctx,state,source,palettes,count,out,size,NULL);
}
int nf_model_texture_indices_owned(NFReadMemory read,void*ctx,const uint8_t context[68],uint8_t**out,uint32_t*width,uint32_t*height){
 if(!read||!context||!out||!width||!height)return 0;
 unsigned shift=h(context+56),rows=h(context+58);uint32_t address=w(context+52);
 if(shift>10||!rows||rows>1024)return 0;
 unsigned columns=1u<<shift;size_t pixels=(size_t)columns*rows;
 if((uint64_t)address+pixels>UINT32_MAX)return 0;
 uint8_t*indices=malloc(pixels);if(!indices)return 0;
 if(!read(ctx,address,indices,pixels)){free(indices);return 0;}
 *out=indices;*width=columns;*height=rows;return 1;
}
static void rgba(uint8_t*out,const uint8_t*palette,unsigned index,int visible);
int nf_extract_model(NFReadMemory read,void*ctx,uint32_t context_address,uint32_t camera_address,uint32_t object_address,const int32_t rotation[12],void**out,size_t*out_size){
 if(!read||!rotation||!out||!out_size)return 0;
 uint8_t context[68],descriptor[40],projection[64],object[164],vertices[2048*6],faces[512],indices[8192],uv_indices[8192],uv[16384],palette[512];int32_t camera[12];
 if(!read(ctx,context_address,context,68)||!read(ctx,w(context+12),descriptor,40)||!read(ctx,w(context+8),projection,64)||!read(ctx,camera_address,camera,48)||!read(ctx,object_address,object,164))return 0;
 unsigned count=h(descriptor+36),face_count=h(descriptor+34),shift=h(context+56),height=h(context+58);
 if(!count||count>2048||!face_count||face_count>512||shift>10||!height||height>1024)return 0;
 unsigned width=1u<<shift;
 if(!indexed_read(read,ctx,w(context+16),w(descriptor),6,vertices,count*6)||!indexed_read(read,ctx,w(context+44),w(descriptor+28),1,faces,face_count))return 0;
 unsigned corners=0;for(unsigned i=0;i<face_count;i++){if(faces[i]<3||faces[i]>32)return 0;corners+=faces[i];}if(corners>4096)return 0;
 if(!indexed_read(read,ctx,w(context+32),w(descriptor+4),2,indices,corners*2)||!indexed_read(read,ctx,w(context+36),w(descriptor+24),2,uv_indices,corners*2))return 0;
 unsigned max_uv=0;for(unsigned i=0;i<corners;i++){if(h(indices+i*2)>=count||h(uv_indices+i*2)>4095)return 0;if(h(uv_indices+i*2)>max_uv)max_uv=h(uv_indices+i*2);}
 if(!indexed_read(read,ctx,w(context+20),(h(descriptor+32)&1)?w(descriptor+8):0,4,uv,(max_uv+1)*4)||!read(ctx,0x05000000,palette,512))return 0;
 NFPoint3 camera_position={-(double)camera[9],-(double)camera[10],-(double)camera[11]},object_position={sw(object+12)/256.0,sw(object+16)/256.0,sw(object+20)/256.0};NFRigidPose poses[2];
 if(!nf_pose_decode(camera,&camera_position,poses)||!nf_pose_decode(rotation,&object_position,poses+1))return 0;
 size_t pixels=(size_t)width*height,size=160+count*24+face_count+corners*18+pixels*4;uint8_t*texture=NULL,*result=malloc(size);uint32_t texture_width,texture_height;
 if(!result)return 0;
 if(!nf_model_texture_indices_owned(read,ctx,context,&texture,&texture_width,&texture_height)||texture_width!=width||texture_height!=height){free(texture);free(result);return 0;}
 uint32_t header[6]={0x324d464e,count,face_count,corners,width,height};memcpy(result,header,24);number(result+24,sh(projection+8));number(result+32,sh(projection+10));number(result+40,w(context+64));memcpy(result+48,poses,sizeof(poses));
 for(unsigned i=0;i<count*3;i++)number(result+160+i*8,sh(vertices+i*2));
 size_t pos=160+count*24;memcpy(result+pos,faces,face_count);pos+=face_count;memcpy(result+pos,indices,corners*2);pos+=corners*2;
 for(unsigned i=0;i<corners;i++){unsigned index=h(uv_indices+i*2);number(result+pos+i*16,h(uv+index*4)/32768.0);number(result+pos+i*16+8,h(uv+index*4+2)/32768.0);}pos+=corners*16;
#ifdef NF_REFERENCE_PALETTE_EXPANSION
 for(size_t i=0;i<pixels;i++)rgba(result+pos+i*4,palette,texture[i],1);
#else
 uint8_t colors[256][4];for(unsigned i=0;i<256;i++)rgba(colors[i],palette,i,1);
 for(size_t i=0;i<pixels;i++)memcpy(result+pos+i*4,colors[texture[i]],4);
#endif
 free(texture);*out=result;*out_size=size;return 1;
}
static void rgba(uint8_t*out,const uint8_t*palette,unsigned index,int visible){
 unsigned color=h(palette+index*2);out[0]=(color&31)*255/31;out[1]=((color>>5)&31)*255/31;out[2]=((color>>10)&31)*255/31;out[3]=visible?255:0;
}
int nf_billboard_view(const void*data,size_t size,NFBillboardView*out){
 if(!data||!out||size<56)return 0;
 const uint8_t*p=data;uint32_t width=w(p+4),height=w(p+8);
 if(w(p)!=0x3142464e||w(p+12)||!width||width>1024||(width&(width-1))||!height||height>1024||size!=56+(size_t)width*height*4)return 0;
 NFBillboardView view;memset(&view,0,sizeof(view));view.width=width;view.height=height;
 memcpy(view.rectangle,p+16,16);memcpy(view.uv,p+32,16);memcpy(view.bounds,p+48,8);
 if(view.rectangle[2]<=view.rectangle[0]||view.rectangle[3]<=view.rectangle[1]||view.bounds[1]<=view.bounds[0]||view.bounds[3]<=view.bounds[2])return 0;
 if(!view.uv[2]||!view.uv[3]||(uint64_t)view.uv[0]+view.uv[2]>width||(uint64_t)view.uv[1]+view.uv[3]>height)return 0;
 view.rgba=p+56;*out=view;return 1;
}
int nf_billboard_quad(const void*data,size_t size,uint32_t width,uint32_t height,double out[16]){
 NFBillboardView v;
 if(!out||!width||!height||width>16384||height>16384||!nf_billboard_view(data,size,&v))return -1;
 double l=v.rectangle[0],t=v.rectangle[1],r=v.rectangle[2],b=v.rectangle[3];
 double cl=l,ct=t,cr=r,cb=b;
 if(cl<v.bounds[0])cl=v.bounds[0];
 if(ct<v.bounds[2])ct=v.bounds[2];
 if(cr>v.bounds[1])cr=v.bounds[1];
 if(cb>v.bounds[3])cb=v.bounds[3];
 if(cl<0)cl=0;
 if(ct<0)ct=0;
 if(cr>240)cr=240;
 if(cb>160)cb=160;
 if(cl>=cr||ct>=cb)return 0;
 double u0=(v.uv[0]+(cl-l)/(r-l)*v.uv[2])/v.width,u1=(v.uv[0]+(cr-l)/(r-l)*v.uv[2])/v.width;
 double v0=(v.uv[1]+(ct-t)/(b-t)*v.uv[3])/v.height,v1=(v.uv[1]+(cb-t)/(b-t)*v.uv[3])/v.height;
 cl*=width/240.0;cr*=width/240.0;ct*=height/160.0;cb*=height/160.0;
 double result[16]={cl,ct,u0,v0,cr,ct,u1,v0,cr,cb,u1,v1,cl,cb,u0,v1};memcpy(out,result,sizeof(result));return 1;
}
int nf_extract_billboard(NFReadMemory read,void*ctx,uint32_t address,uint32_t state_address,void**out,size_t*out_size){
 if(!read||!out||!out_size)return 0;
 uint8_t context[44],rect[16],bounds[8],palette[512];
 if(state_address>UINT32_MAX-0xe2||!read(ctx,address,context,44)||!read(ctx,w(context+12),rect,16)||!read(ctx,state_address+0xe2,bounds,8)||!read(ctx,0x05000000,palette,512))return 0;
 unsigned shift=h(context+36),height=h(context+38);
 if(shift>10||!height||height>1024)return 0;
 unsigned width=1u<<shift;size_t pixels=(size_t)width*height,size=56+pixels*4;
 if((uint64_t)w(context+40)+pixels>0x100000000ull)return 0;
 uint8_t*indices=malloc(pixels),*result=malloc(size);
 if(!indices||!result){free(indices);free(result);return 0;}
 if(!read(ctx,w(context+40),indices,pixels)){free(indices);free(result);return 0;}
 uint32_t header[4]={0x3142464e,width,height,0};memcpy(result,header,16);memcpy(result+16,rect,16);memcpy(result+32,context+16,16);memcpy(result+48,bounds,8);
#ifdef NF_REFERENCE_PALETTE_EXPANSION
 for(size_t i=0;i<pixels;i++)rgba(result+56+i*4,palette,indices[i],indices[i]!=0);
#else
 uint8_t colors[256][4];for(unsigned i=0;i<256;i++)rgba(colors[i],palette,i,i!=0);
 for(size_t i=0;i<pixels;i++)memcpy(result+56+i*4,colors[indices[i]],4);
#endif
 free(indices);*out=result;*out_size=size;return 1;
}
typedef struct {uint8_t palette[512],table[4096],colors[16][256][4];int ready;} NFWallShadeLookup;
static __thread NFWallShadeLookup wall_shade_lookup;
static __thread uint64_t wall_shade_stats[2];
__declspec(dllexport) void nf_wall_shade_lookup_stats(uint64_t out[2]){if(out)memcpy(out,wall_shade_stats,sizeof(wall_shade_stats));}
__declspec(dllexport) int nf_wall_shade_lookup(const uint8_t palette[512],const uint8_t table[4096],uint8_t out[16][256][4]){
 if(!palette||!table||!out)return 0;
 NFWallShadeLookup*c=&wall_shade_lookup;
 if(getenv("NF_TEST_WALL_SHADE_LOOKUP_CACHE")&&c->ready&&!memcmp(c->palette,palette,512)&&!memcmp(c->table,table,4096)){memcpy(out,c->colors,sizeof(c->colors));wall_shade_stats[0]++;return 1;}
 wall_shade_stats[1]++;
 for(unsigned level=0;level<16;level++)for(unsigned i=0;i<256;i++)rgba(out[level][i],palette,table[i*16+level],i!=0);
 if(getenv("NF_TEST_WALL_SHADE_LOOKUP_CACHE")){memcpy(c->palette,palette,512);memcpy(c->table,table,4096);memcpy(c->colors,out,sizeof(c->colors));c->ready=1;}
 return 1;
}
int nf_extract_wall(NFReadMemory read,void*ctx,uint32_t state_address,uint32_t descriptor_address,uint32_t source_address,uint32_t material_address,uint32_t resolved_address,uint32_t flags,void**out,size_t*out_size,void**out_light,size_t*out_light_size){
 if(!read||!out||!out_size||!out_light||!out_light_size||(flags&128))return 0;
 uint8_t state[256],descriptor[48],source[68],next[68],offset[32]={0},next_offset[32]={0},material[48],resolved[32],animation[8],palette[512],table[4096],context[24];
 if(!read(ctx,state_address,state,256)||!read(ctx,descriptor_address,descriptor,48)||!read(ctx,source_address,source,68)||!read(ctx,material_address,material,48)||!read(ctx,resolved_address,resolved,32))return 0;
 unsigned count=h(descriptor+2),shift=h(material+36),height=h(material+38);uint64_t base=(uint64_t)w(state+16)+h(descriptor)*68;
 if(!count||count>32||base>source_address||(source_address-base)%68||(source_address-base)/68>=count||shift>10||!height||height>1024)return 0;
 unsigned index=(unsigned)(source_address-base)/68,next_index=(index+1)%count,width=1u<<shift;
 if(base+next_index*68>UINT32_MAX||!read(ctx,(uint32_t)(base+next_index*68),next,68))return 0;
 if(h(source+42)!=65535&&!indexed_read(read,ctx,w(state+24),h(source+42),32,offset,32))return 0;
 if(h(next+42)!=65535&&!indexed_read(read,ctx,w(state+24),h(next+42),32,next_offset,32))return 0;
 if(!indexed_read(read,ctx,w(state+72),h(resolved),8,animation,8)||!read(ctx,0x05000000,palette,512))return 0;
 unsigned lit=!(flags&256);if(lit&&(!read(ctx,w(material+8),context,24)||!read(ctx,w(context+20),table,4096)||source[60]>15||source[61]>15))return 0;
 size_t pixels=(size_t)width*height,size=172+pixels*4,light_size=lit?20+pixels*64:4;
 if(size+light_size>64*1024*1024)return 0;
 uint8_t*texture=malloc(pixels),*surface=malloc(size),*light=malloc(light_size);
 if(!texture||!surface||!light){free(texture);free(surface);free(light);return 0;}
 if(!read(ctx,w(material+40),texture,pixels)){free(texture);free(surface);free(light);return 0;}
 uint32_t header[3]={4,width,height};memcpy(surface,header,12);
 double x=(double)sw(source)+sh(offset),z=(double)sw(source+4)+sh(offset+2),nx=(double)sw(next)+sh(next_offset),nz=(double)sw(next+4)+sh(next_offset+2);
 double vertices[12]={x,sh(source+8)+sh(offset+8),z,nx,sh(source+12)+sh(offset+8),nz,nx,sh(source+14)+sh(offset+10),nz,x,sh(source+10)+sh(offset+10),z};memcpy(surface+12,vertices,sizeof(vertices));
 double start=h(source+40)/(double)width+sh(animation+4)/(256.0*width),end=start+h(source+64)/256.0;if(flags&2){double t=start;start=end;end=t;}
 double top=((double)sw(source+16)+(sh(animation+6)>>1))/(128.0*height),span=((double)sw(source+24)+(sh(animation+6)>>1))/(128.0*height);
 double uv[8]={start,top,end,top,end,top+span,start,top+span};memcpy(surface+108,uv,sizeof(uv));
 uint8_t base_colors[256][4];for(unsigned i=0;i<256;i++)rgba(base_colors[i],palette,i,i!=0);
 for(size_t i=0;i<pixels;i++)memcpy(surface+172+i*4,base_colors[texture[i]],4);
 memcpy(light,&lit,4);if(lit){uint32_t info[4]={source[60],source[61],width,height};memcpy(light+4,info,16);
  uint8_t colors[16][256][4];nf_wall_shade_lookup(palette,table,colors);
  for(unsigned level=0;level<16;level++)for(size_t i=0;i<pixels;i++)memcpy(light+20+(level*pixels+i)*4,colors[level][texture[i]],4);
 }
 free(texture);*out=surface;*out_size=size;*out_light=light;*out_light_size=light_size;return 1;
}
int nf_road_material_plan_layer(NFReadMemory read,void*ctx,uint32_t state_address,uint32_t descriptor_address,unsigned layer,uint32_t out[5]){
 uint8_t state[256],descriptor[48],material[32],animation[8];
 if(!read||!out||layer>1||!read(ctx,state_address,state,256)||!read(ctx,descriptor_address,descriptor,48))return 0;
 unsigned index=h(descriptor+(layer?4:8));if(!index)return 0;
 if(!indexed_read(read,ctx,w(state+32),index,32,material,32))return 0;
 uint64_t uv=(uint64_t)w(state+72)+h(material)*8ull;
 if(uv>UINT32_MAX||!read(ctx,(uint32_t)uv,animation,8))return 0;
 uint64_t resolved=(uint64_t)w(state+32)+(index+h(animation+2))*32ull;
 if(resolved>UINT32_MAX||!read(ctx,(uint32_t)resolved,material,32))return 0;
 uint64_t texture=(uint64_t)w(state)+w(material+4);
 if(texture>UINT32_MAX||h(material+26)>10||!h(material+10)||h(material+10)>1024)return 0;
 uint32_t result[5]={(uint32_t)resolved,(uint32_t)uv,(uint32_t)texture,h(material+26),h(material+10)};
 memcpy(out,result,sizeof(result));return 1;
}
int nf_road_material_plan(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,uint32_t out[5]){return nf_road_material_plan_layer(read,ctx,state,descriptor,0,out);}
int nf_road_source_attributes_layer_owned(NFReadMemory read,void*ctx,uint32_t state_address,uint32_t descriptor_address,unsigned affine,unsigned layer,NFRoadSourceAttributes*out){
 if(!read||!out||affine>1||layer>1)return 0;
 uint8_t state[256],descriptor[48],animation[8],source[32*68];uint32_t plan[5];NFRoadSourceAttributes result={0};
 if(!read(ctx,state_address,state,256)||!read(ctx,descriptor_address,descriptor,48)||!h(descriptor+(layer?4:8)))return 0;
 unsigned count=h(descriptor+2);if(count<3||count>32)return 0;
 if(!nf_road_material_plan_layer(read,ctx,state_address,descriptor_address,layer,plan)||plan[3]>10||plan[4]<2||(plan[4]&1)||!read(ctx,plan[1],animation,8))return 0;
 if(!indexed_read(read,ctx,w(state+16),h(descriptor),68,source,count*68))return 0;
 if(layer){uint8_t projection_material[32];unsigned index=h(descriptor+8)?h(descriptor+8):h(descriptor+4);if(!indexed_read(read,ctx,w(state+32),index,32,projection_material,32)||h(projection_material+26)!=plan[3]||h(projection_material+10)!=plan[4])return 0;}
 result.count=count;result.shift=plan[3];result.stored_height=plan[4];result.affine=affine;result.material=plan[0];result.animation=plan[1];
 result.offsets[0]=sh(animation+4);result.offsets[1]=sh(animation+6);
 for(unsigned i=0;i<count;i++){result.attributes[i][0]=sw(source+i*68+32);result.attributes[i][1]=sw(source+i*68+36);}
 memcpy(out,&result,sizeof(result));return 1;
}
int nf_road_source_attributes_owned(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,unsigned affine,NFRoadSourceAttributes*out){uint8_t d[48];if(!read||!read(ctx,descriptor,d,48)||h(d+4))return 0;return nf_road_source_attributes_layer_owned(read,ctx,state,descriptor,affine,0,out);}
int nf_scene_command_road_attributes_owned(const NFNativeSceneCommand*command,NFReadMemory read,void*user,NFRoadSourceAttributes*out){
 if(!command||command->kind!=1||command->xyz[2]>1||command->xyz[1]>1||!read||!out)return 0;
 NFCommandAssetReader owned={0};owned.command=command;owned.read=read;owned.user=user;NFRoadSourceAttributes result;
 if(!nf_road_source_attributes_layer_owned(command_asset_read,&owned,0xfffe0000u,command->source,command->xyz[1],command->xyz[2],&result))return 0;
 if(result.material!=command->material[0]||result.shift!=command->material[2]||result.stored_height!=command->material[3])return 0;
 memcpy(out,&result,sizeof(result));return 1;
}
int nf_road_texture_indices_layer_owned(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,unsigned layer,uint8_t**out,uint32_t*out_width,uint32_t*out_height){
 uint32_t plan[5];if(!out||!out_width||!out_height||!nf_road_material_plan_layer(read,ctx,state,descriptor,layer,plan)||plan[3]<1||plan[4]<2||(plan[4]&(plan[4]-1)))return 0;
 unsigned width=1u<<plan[3],height=plan[4]/2;size_t pixels=(size_t)width*height,packed_size=pixels*2;
 if(packed_size-1>UINT32_MAX-plan[2])return 0;
 uint8_t*packed=malloc(packed_size),*indices=malloc(pixels);if(!packed||!indices){free(packed);free(indices);return 0;}
 if(!read(ctx,plan[2],packed,packed_size)){free(packed);free(indices);return 0;}
 for(unsigned y=0;y<height;y++)memcpy(indices+(size_t)y*width,packed+(size_t)y*width*2,width);
 free(packed);*out=indices;*out_width=width;*out_height=height;return 1;
}
int nf_road_texture_indices_owned(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,uint8_t**out,uint32_t*w,uint32_t*h){return nf_road_texture_indices_layer_owned(read,ctx,state,descriptor,0,out,w,h);}
int nf_extract_road_candidate_layer(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,const uint8_t*palettes,unsigned count,unsigned layer,void**out,size_t*size){
 uint32_t plan[5];
 if(!out||!size||!palettes||!count||count>256||!nf_road_material_plan_layer(read,ctx,state,descriptor,layer,plan)||plan[4]<2||(plan[4]&1))return 0;
 unsigned width=1u<<plan[3],height=plan[4]/2;size_t pixels=(size_t)width*height;
 uint8_t*packed=malloc(pixels*2),*indices=malloc(pixels);
 if(!packed||!indices){free(packed);free(indices);return 0;}
 CandidateReader reader={0};reader.read=read;reader.ctx=ctx;
 int ok=read(ctx,plan[2],packed,pixels*2);
 if(ok){for(unsigned y=0;y<height;y++)memcpy(indices+(size_t)y*width,packed+(size_t)y*width*2,width);ok=nf_candidate_palette(indices,pixels,palettes,count,reader.palette);}
 free(packed);free(indices);if(!ok)return 0;
 uint16_t shift=(uint16_t)plan[3],stored=(uint16_t)plan[4];
 memcpy(reader.material+36,&shift,2);memcpy(reader.material+38,&stored,2);memcpy(reader.material+40,plan+2,4);
 return nf_extract_road_layer(candidate_read,&reader,state,descriptor,0xffff0000u,plan[1],layer,out,size);
}
int nf_extract_road_candidate(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,const uint8_t*palettes,unsigned count,void**out,size_t*size){uint8_t d[48];if(!read||!read(ctx,descriptor,d,48)||h(d+4))return 0;return nf_extract_road_candidate_layer(read,ctx,state,descriptor,palettes,count,0,out,size);}
int nf_extract_road_layer(NFReadMemory read,void*ctx,uint32_t state_address,uint32_t descriptor_address,uint32_t material_address,uint32_t uv_address,unsigned layer,void**out,size_t*out_size){
 if(!read||!out||!out_size)return 0;
 uint8_t state[256],descriptor[48],material[48],uv[8],source[32*68],offsets[32][32]={{0}},face[20]={0},palette[512];
 if(!read(ctx,state_address,state,sizeof(state))||!read(ctx,descriptor_address,descriptor,sizeof(descriptor))||!read(ctx,material_address,material,sizeof(material))||!read(ctx,uv_address,uv,sizeof(uv)))return 0;
 unsigned count=h(descriptor+2),shift=h(material+36),stored_height=h(material+38);
 if(layer>1||count<3||count>32||!h(descriptor+(layer?4:8))||shift>10||stored_height<2||stored_height>1024||(stored_height&1))return 0;
 if(layer){uint8_t projection_material[32];unsigned index=h(descriptor+8)?h(descriptor+8):h(descriptor+4);if(!indexed_read(read,ctx,w(state+32),index,32,projection_material,32)||h(projection_material+26)!=shift||h(projection_material+10)!=stored_height)return 0;}
 unsigned width=1u<<shift,height=stored_height/2;
 if(!indexed_read(read,ctx,w(state+16),h(descriptor),68,source,count*68))return 0;
 unsigned face_index=h(descriptor+10);if(face_index!=65535&&!indexed_read(read,ctx,w(state+28),face_index,20,face,20))return 0;
 for(unsigned i=0;i<count;i++){unsigned index=h(source+i*68+42);if(index!=65535&&!indexed_read(read,ctx,w(state+24),index,32,offsets[i],32))return 0;}
 if(!read(ctx,0x05000000,palette,512))return 0;
 size_t packed_size=(size_t)width*stored_height,total=12+count*40+(size_t)width*height*4;
 uint8_t*packed=malloc(packed_size),*result=malloc(total);if(!packed||!result){free(packed);free(result);return 0;}
 if(!read(ctx,w(material+40),packed,packed_size)){free(packed);free(result);return 0;}
 uint32_t header[3]={count,width,height};memcpy(result,header,12);
 for(unsigned i=0;i<count;i++){
  const uint8_t*s=source+i*68,*o=offsets[i];uint8_t*v=result+12+i*24,*t=result+12+count*24+i*16;
  number(v,(double)sw(s)+sh(o));number(v+8,(double)sh(s+(layer?58:56))+sh(o+(layer?4:6))+sh(face+(layer?4:6)));number(v+16,(double)sw(s+4)+sh(o+2));
  number(t,sw(s+32)/16384.0+sh(uv+4)/(256.0*width));number(t+8,sw(s+36)/16384.0+sh(uv+6)/(512.0*height));
 }
#ifndef NF_REFERENCE_PALETTE_EXPANSION
 uint8_t colors[256][4];for(unsigned i=0;i<256;i++)rgba(colors[i],palette,i,1);
#endif
 uint8_t*rgba=result+12+count*40;
 for(unsigned y=0;y<height;y++)for(unsigned x=0;x<width;x++){
#ifdef NF_REFERENCE_PALETTE_EXPANSION
  unsigned color=h(palette+packed[y*width*2+x]*2);*rgba++=(color&31)*255/31;*rgba++=((color>>5)&31)*255/31;*rgba++=((color>>10)&31)*255/31;*rgba++=255;
#else
  memcpy(rgba,colors[packed[y*width*2+x]],4);rgba+=4;
#endif
 }
 free(packed);*out=result;*out_size=total;return 1;
}


int nf_extract_road(NFReadMemory read,void*ctx,uint32_t state,uint32_t descriptor,uint32_t material,uint32_t uv,void**out,size_t*size){uint8_t d[48];if(!read||!read(ctx,descriptor,d,48)||h(d+4))return 0;return nf_extract_road_layer(read,ctx,state,descriptor,material,uv,0,out,size);}
static int asset_colors_equal(const uint8_t*a,const uint8_t*b,size_t size,size_t header){
 if(size<header||memcmp(a,b,header)||(size-header)%4)return 0;
 for(size_t i=header;i<size;i+=4)if((a[i+3]||b[i+3])&&memcmp(a+i,b+i,4))return 0;
 return 1;
}
static uint32_t command_palette_detail[4];
static uint64_t command_palette_stats[6];
void nf_scene_command_palette_stats(uint64_t out[6]){if(out)memcpy(out,command_palette_stats,sizeof(command_palette_stats));}
int nf_scene_command_palette_consensus_extract(const NFDrawPalettes*a,uint32_t sa,const NFDrawPalettes*b,uint32_t sb,uint64_t epoch,const NFNativeSceneCommand*c,NFReadMemory read,void*user,const int32_t rotation[12],uint8_t out[512],void**asset_out,size_t*asset_size,void**light_out,size_t*light_size){
 command_palette_stats[4]++;
 if(!a||!b||!c||!read||!out||!asset_out||!asset_size||!light_out||!light_size||(c->kind!=1&&c->kind!=2))return 0;
 uint8_t*palettes=malloc(256*512);if(!palettes)return 0;unsigned count=0;int ok=1;
 const NFDrawPalettes*banks[2]={a,b};uint32_t serials[2]={sa,sb};
 for(unsigned j=0;j<2&&ok;j++)for(unsigned i=0;i<256;i++){
  uint32_t key[3];uint8_t colors[512];if(!nf_draw_palettes_key(banks[j],i,key))break;
  if(key[0]!=1&&key[0]!=2)continue;
  if(!nf_draw_palettes_read(banks[j],epoch,serials[j],i,key[0],key[1],key[2],colors,512)){ok=0;break;}
  unsigned n=0;for(;n<count;n++)if(!memcmp(palettes+n*512,colors,512))break;
  if(n==count){if(count==256){ok=0;break;}memcpy(palettes+count++*512,colors,512);}
 }
 void*reference=NULL,*reference_light=NULL;size_t reference_size=0,reference_light_size=0;
 for(unsigned i=0;i<count&&ok;i++){
  void*asset=NULL,*light=NULL;size_t size=0,light_size=0;
  command_palette_stats[5]++;ok=nf_extract_scene_command_full(c,read,user,palettes+i*512,rotation,&asset,&size,&light,&light_size,NULL);
  if(ok&&!i){reference=asset;reference_light=light;reference_size=size;reference_light_size=light_size;continue;}
  if(ok){size_t header=12+(size_t)w(asset)*40;ok=size==reference_size&&light_size==reference_light_size&&asset_colors_equal(reference,asset,size,header);if(ok&&light_size)ok=asset_colors_equal(reference_light,light,light_size,light_size==4?4:20);}
  free(asset);free(light);
 }
 if(ok&&count){memcpy(out,palettes,512);*asset_out=reference;*asset_size=reference_size;*light_out=reference_light;*light_size=reference_light_size;free(palettes);return 1;}
 free(reference);free(reference_light);free(palettes);return 0;
}
int nf_scene_command_palette_consensus(const NFDrawPalettes*a,uint32_t sa,const NFDrawPalettes*b,uint32_t sb,uint64_t epoch,const NFNativeSceneCommand*c,NFReadMemory read,void*user,const int32_t rotation[12],uint8_t out[512]){
 void*asset=NULL,*light=NULL;size_t size=0,light_size=0;
 int ok=nf_scene_command_palette_consensus_extract(a,sa,b,sb,epoch,c,read,user,rotation,out,&asset,&size,&light,&light_size);
 free(asset);free(light);return ok;
}
void nf_scene_command_palette_detail(uint32_t out[4]){if(out)memcpy(out,command_palette_detail,16);}
int nf_scene_command_palette_extract(const NFDrawPalettes*bank,uint64_t epoch,uint32_t serial,const NFNativeSceneCommand*c,NFReadMemory read,void*user,const int32_t rotation[12],uint8_t out[512],void**asset_out,size_t*asset_size,void**light_out,size_t*light_size){
 command_palette_stats[0]++;
 memset(command_palette_detail,0,16);
 if(!bank||!c||!read||!out||!asset_out||!asset_size||!light_out||!light_size||(c->kind!=1&&c->kind!=2))return 0;
 uint32_t material=c->material[c->kind==1?1:0];uint8_t chosen[512],palette[512];void*reference=NULL,*reference_light=NULL;size_t reference_size=0,reference_light_size=0;int found=0,ok=1;
 for(unsigned i=0;i<256&&ok;i++){
  uint32_t key[3];if(!nf_draw_palettes_key(bank,i,key))break;
  if(key[0]!=c->kind||key[1]!=c->source||key[2]!=material)continue;
  command_palette_detail[1]++;
  command_palette_stats[1]++;
  void*asset=NULL,*light=NULL;size_t size=0,light_size=0;
  ok=nf_draw_palettes_read(bank,epoch,serial,i,key[0],key[1],key[2],palette,512);
  /* Sealed palette bank and scene-owned reader: identical palette bytes
     cannot change the already validated extraction for this command. */
  if(ok&&found&&!memcmp(chosen,palette,512)){command_palette_stats[2]++;continue;}
  if(ok){unsigned extraction_stage=0;command_palette_stats[3]++;ok=nf_extract_scene_command_full(c,read,user,palette,rotation,&asset,&size,&light,&light_size,&extraction_stage);if(!ok)command_palette_detail[2]=extraction_stage;}
  if(!ok)command_palette_detail[0]=2;
  if(ok&&!found){reference=asset;reference_light=light;reference_size=size;reference_light_size=light_size;memcpy(chosen,palette,512);found=1;continue;}
  if(ok){size_t header=12+(size_t)w(asset)*40;ok=size==reference_size&&light_size==reference_light_size&&asset_colors_equal(reference,asset,size,header);
   if(!ok)command_palette_detail[0]=3;
   if(ok&&light_size){ok=asset_colors_equal(reference_light,light,light_size,light_size==4?4:20);if(!ok)command_palette_detail[0]=4;}
  }
  free(asset);free(light);
 }
 if(!ok||!found){free(reference);free(reference_light);if(!found&&!command_palette_detail[0])command_palette_detail[0]=1;return 0;}
 memcpy(out,chosen,512);*asset_out=reference;*asset_size=reference_size;*light_out=reference_light;*light_size=reference_light_size;return 1;
}
int nf_scene_command_palette(const NFDrawPalettes*bank,uint64_t epoch,uint32_t serial,const NFNativeSceneCommand*c,NFReadMemory read,void*user,const int32_t rotation[12],uint8_t out[512]){
 void*asset=NULL,*light=NULL;size_t size=0,light_size=0;
 int ok=nf_scene_command_palette_extract(bank,epoch,serial,c,read,user,rotation,out,&asset,&size,&light,&light_size);
 free(asset);free(light);return ok;
}

