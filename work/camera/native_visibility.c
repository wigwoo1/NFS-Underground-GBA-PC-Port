/* Synchronous research diagnostic; not a thread-safe error channel. */
static unsigned visibility_failure_stage;
__declspec(dllexport) unsigned nfs_visibility_failure_stage(void){return visibility_failure_stage;}
#include "native_visibility.h"
__declspec(dllexport) unsigned nfs_visibility_queue_capacity(void){return NF_VISIBILITY_QUEUE_CAPACITY;}
#include <string.h>
static uint32_t word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static uint16_t half(const uint8_t*p){uint16_t v;memcpy(&v,p,2);return v;}
static void put(uint8_t*p,uint16_t v){memcpy(p,&v,2);}
static uint32_t sar(uint32_t v,unsigned n){return (v>>n)|((v&0x80000000u)?(~0u<<(32-n)):0);}
__declspec(dllexport) int nfs_visibility_billboard_raster(const uint32_t c[8],uint32_t shift,const uint8_t*texture,uint32_t texture_bytes,uint8_t*framebuffer,uint32_t framebuffer_bytes,uint32_t stride){
 if(!c||!texture||!framebuffer||shift>15||!stride||(stride&1)||!c[2]||!c[3]||c[2]>32768||c[3]>32768||(int32_t)c[0]<0||(int32_t)c[1]<0)return 0;
 /* Two passes ensure a late invalid sample cannot leave a partial frame. */
 for(unsigned pass=0;pass<2;pass++){
  uint32_t v=c[5];
  for(uint32_t y=0;y<c[3];y++,v+=c[7]){
   int32_t row=(int32_t)sar(v,16);if(row<0)return 0;
   uint64_t source=(uint64_t)(uint32_t)row<<shift;
   uint64_t dest=((uint64_t)c[1]+y)*stride+(c[0]&~1u);
   uint32_t u=c[4];
   for(uint32_t x=0;x<c[2];x++,u+=c[6]){
    uint64_t src=source+(u>>16),dst=dest+2ull*x;
    if(src>=texture_bytes||dst>=framebuffer_bytes)return 0;
    if(pass&&texture[src])framebuffer[dst]=texture[src];
   }
  }
 }
 return 1;
}
__declspec(dllexport) int nfs_visibility_object_billboard_prepare(const uint8_t object[164],const uint8_t material[32],const uint8_t next[32],const uint32_t p[9],const uint16_t bounds[4],const uint32_t reciprocal[32768],uint32_t out[18]){
 if(!p||!out)return -2;
 uint32_t result[18],mp[4]={p[2],p[6],p[7],p[8]};
 if(!nfs_visibility_object_rect(object,material,p,reciprocal,result)||!nfs_visibility_object_billboard_material(material,next,mp,result+4))return -2;
 uint32_t uv[4]={0,0,result[4],result[5]};
 int status=nfs_visibility_billboard_clip(result,uv,bounds,reciprocal,result+10);
 if(status!=1)return status;
 memcpy(out,result,sizeof(result));return 1;
}
/* Billboard clip setup; output remains unchanged for rejected rectangles. */
__declspec(dllexport) int nfs_visibility_billboard_clip(const uint32_t rect[4],const uint32_t uv[4],const uint16_t bounds[4],const uint32_t reciprocal[32768],uint32_t out[8]){
 if(!rect||!uv||!bounds||!reciprocal||!out)return -2;
 uint32_t x=rect[0],y=rect[2],w=rect[1]-x,h=rect[3]-y;
 if(!w||!h)return -1;
 if(w>=32768||h>=32768)return -2;
 uint32_t du=sar(reciprocal[w],8),dv=sar(reciprocal[h],8);
 uint32_t u=uv[0]<<16,v=uv[1]<<16,stepu=(du*uv[2])<<1,stepv=dv*uv[3];
 if((int32_t)y<(int32_t)bounds[2]){
  if((int32_t)rect[3]<(int32_t)bounds[2])return -5;
  uint32_t d=bounds[2]-y;v+=dv*(d*uv[3]);y=bounds[2];h-=d;
 }
 if((int32_t)rect[3]>=(int32_t)bounds[3]){
  if((int32_t)y>=(int32_t)bounds[3])return -5;
  h-=rect[3]-bounds[3];
 }
 if((int32_t)x<(int32_t)bounds[0]){
  if((int32_t)rect[1]<(int32_t)bounds[0])return -5;
  uint32_t d=bounds[0]-x;u+=du*(d*uv[2]);x=bounds[0];w-=d;
 }
 if((int32_t)rect[1]>=(int32_t)bounds[1]){
  if((int32_t)x>=(int32_t)bounds[1])return -5;
  w-=rect[1]-bounds[1];
 }
 w=sar(w,1)+1;if((int32_t)h<=0||(int32_t)w<=0)return -5;
 uint32_t result[8]={x,y,w,h,u,v,stepu,stepv};memcpy(out,result,sizeof(result));return 1;
}
__declspec(dllexport) int nfs_visibility_object_billboard_material(const uint8_t material[32],const uint8_t next[32],const uint32_t p[4],uint32_t out[6]){
 if(!material||!p||!out)return 0;
 uint32_t w=half(material+8),h=half(material+10),texture=p[3],offset=0;
 if(half(material+0x16)||half(material+0x18)){w=half(material+0x16);h=half(material+0x18);}
 if((int32_t)p[0]>=4096&&!p[1]&&!(half(material+2)&16)){
  if(!next)return 0;
  offset=32;w>>=2;h>>=2;texture=p[2]+word(next+4);material=next;
 }
 uint32_t result[6]={w,h,texture,half(material+0x1a),half(material+10),offset};
 memcpy(out,result,sizeof(result));return 1;
}
__declspec(dllexport) int nfs_visibility_object_billboard_plan(const uint8_t state[256],const uint8_t object[164],const uint32_t xyz[3],const uint32_t plan[4],NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint32_t out[18]){
 if(!state||!object||!xyz||!plan||!read||!reciprocal||!out||plan[3]!=1)return -2;
 uint8_t material[32],next[32],projection[32];
 if(!read(context,plan[0],material,32)||!read(context,word(state+80),projection,32))return -2;
 uint32_t sb=(uint32_t)(int32_t)(int16_t)half(object+54);const uint8_t*following=NULL;
 if((int32_t)plan[1]>=4096&&!sb&&!(half(material+2)&16)){
  if(!read(context,plan[0]+32,next,32))return -2;
  following=next;
 }
 uint32_t params[9]={xyz[0],xyz[1],plan[1],word(projection+28),(uint32_t)(int32_t)(int16_t)half(projection+8),(uint32_t)(int32_t)(int16_t)half(projection+10),sb,word(state+4),plan[2]};
 uint16_t bounds[4]={half(state+226),half(state+228),half(state+230),half(state+232)};
 return nfs_visibility_object_billboard_prepare(object,material,following,params,bounds,reciprocal,out);
}
__declspec(dllexport) int nfs_visibility_object_rect(const uint8_t object[164],const uint8_t material[32],const uint32_t p[6],const uint32_t reciprocal[8192],uint32_t out[4]){
 if(!object||!material||!p||!reciprocal||!out||p[2]>=8192)return 0;
 uint32_t size=(uint32_t)(int32_t)(int16_t)half(object+0x70),w=sar(size*half(material+8),9),h=sar(size*half(material+10),9);
 uint32_t factor=sar(reciprocal[p[2]]*p[3],8);
 uint32_t rect[4]={p[4]+sar(factor*(p[0]-w),16),p[4]+sar(factor*(p[0]+w),16),p[5]+sar(factor*(p[1]-(h<<1)),16),p[5]+sar(factor*p[1],16)};
 memcpy(out,rect,16);return 1;
}
__declspec(dllexport) int nfs_visibility_object_model_context(const uint8_t state[256],const uint8_t object[164],const uint8_t material[32],const uint32_t p[4],NFVisibilityRead read,void*user,uint8_t context[68]){
 if(!state||!object||!material||!p||!read||!context)return -1;
 if(object[0x88]==255)return 0;
 uint32_t index=(uint32_t)(int32_t)(int16_t)half(object+0x36);
 if((int32_t)p[0]>=512)index++;
 uint32_t descriptor=word(state+0x7c)+(index-1)*40;uint8_t flags[2],out[68];
 if(!read(user,descriptor+32,flags,2))return -1;
 memcpy(out,context,68);
 uint32_t pairs[][2]={{8,p[1]},{12,descriptor},{16,word(state+0x80)},{20,(half(flags)&1)?word(state+0x90):0},{32,word(state+0x84)},{36,word(state+0x88)},{44,word(state+0x9c)},{48,word(state+0xa0)},{52,p[2]},{60,word(state+0xfc)+(uint32_t)object[0x88]*48},{64,p[3]}};
 for(unsigned i=0;i<sizeof(pairs)/sizeof(pairs[0]);i++)memcpy(out+pairs[i][0],&pairs[i][1],4);
 put(out+56,half(material+0x1a));put(out+58,half(material+10));memcpy(context,out,68);return 1;
}
__declspec(dllexport) int nfs_visibility_object_model_plan(const uint8_t state[256],const uint8_t object[164],const uint32_t plan[4],NFVisibilityRead read,void*user,uint8_t context[68]){
 if(!state||!object||!plan||!read||!context||plan[3])return -1;
 if(object[0x88]==255)return 0;
 uint8_t material[32],projection[32];uint32_t address=word(state+80);
 if(!read(user,plan[0],material,32)||!read(user,address,projection,32))return -1;
 uint32_t params[4]={plan[1],address,plan[2],word(projection+28)};
 return nfs_visibility_object_model_context(state,object,material,params,read,user,context);
}
__declspec(dllexport) int nfs_visibility_object_texture(const uint8_t object[164],const uint8_t material[32],const uint8_t previous[32],uint32_t texture_base,uint32_t depth,uint32_t out[2]){
 if(!object||!material||!out)return 0;
 uint32_t texture;
 if(half(object+10)&8){
  texture=word(object+0x84);
  if((int32_t)depth>1024){if(!previous)return 0;texture+=(uint32_t)half(previous+8)*half(previous+10);}
 }else texture=texture_base+word(material+4);
 out[0]=texture;out[1]=(int32_t)depth>1024||half(object+0x36)==0;return 1;
}
__declspec(dllexport) int nfs_visibility_object_material(uint8_t object[164],uint32_t base,uint32_t depth,uint32_t out[2]){
 if(!object||!out)return 0;
 unsigned flags=half(object+10);uint32_t address=base+(uint32_t)half(object+0x48)*32;
 if(flags&2)depth=0;
 if(half(object+0x36)!=0&&(int32_t)depth>1024){if(flags&64)depth=512;else address+=32;}
 address+=((uint32_t)half(object+0x46)+(half(object+0x44)>>8))*32;
 put(object+10,(uint16_t)(flags|4));out[0]=address;out[1]=depth;return 1;
}
__declspec(dllexport) int nfs_visibility_object_visible(const uint32_t p[6],const uint32_t reciprocal[8192]){
 if(!p||!reciprocal)return -1;
 if(p[1]>=8192)return 0;
 uint32_t factor=sar(reciprocal[p[1]]*p[2],8),radius=sar(factor<<9,16);
 uint32_t y=p[3]+sar(factor*p[0],16);
 if((int32_t)y<=(int32_t)(p[4]-radius)||(int32_t)y>=(int32_t)(p[5]+radius))return 0;
 return 1;
}
__declspec(dllexport) int nfs_visibility_object_material_plan(const uint8_t state[256],uint8_t object[164],const uint32_t xyz[3],NFVisibilityRead read,void*context,const uint32_t reciprocal[8192],uint32_t out[4]){
 if(!state||!object||!xyz||!read||!reciprocal||!out||(half(object+10)&16))return -1;
 if(xyz[2]>=8192)return 0;
 uint8_t projection[32],owned[164],material[32],previous[32];uint32_t result[4],texture[2];
 if(!read(context,word(state+80),projection,32))return -1;
 uint32_t params[6]={xyz[1],xyz[2],word(projection+28),(uint32_t)(int32_t)(int16_t)half(projection+10),half(state+230),half(state+232)};
 int visible=nfs_visibility_object_visible(params,reciprocal);if(visible!=1)return visible;
 memcpy(owned,object,164);if(!nfs_visibility_object_material(owned,word(state+36),xyz[2],result))return -1;
 if(!read(context,result[0],material,32))return -1;
 const uint8_t*prior=NULL;
 if((half(owned+10)&8)&&(int32_t)result[1]>1024){if(!read(context,result[0]-32,previous,32))return -1;prior=previous;}
 if(!nfs_visibility_object_texture(owned,material,prior,word(state+4),result[1],texture))return -1;
 result[2]=texture[0];result[3]=texture[1];memcpy(object,owned,164);memcpy(out,result,16);return 1;
}
__declspec(dllexport) int nfs_visibility_callback_state(uint8_t b[32],uint32_t m[12],uint32_t g[2],const uint8_t bb[32],const uint8_t ab[32],const uint32_t bm[12],const uint32_t am[12],const uint32_t bg[2],const uint32_t ag[2]){
 if(!b||!m||!g||!bb||!ab||!bm||!am||!bg||!ag)return 0;
 for(unsigned i=0;i<32;i++)if(bb[i]!=ab[i]&&b[i]!=bb[i])return 0;
 for(unsigned i=0;i<12;i++)if(bm[i]!=am[i]&&m[i]!=bm[i])return 0;
 for(unsigned i=0;i<2;i++)if(bg[i]!=ag[i]&&g[i]!=bg[i])return 0;
 for(unsigned i=0;i<32;i++)if(bb[i]!=ab[i])b[i]=ab[i];
 for(unsigned i=0;i<12;i++)if(bm[i]!=am[i])m[i]=am[i];
 for(unsigned i=0;i<2;i++)if(bg[i]!=ag[i])g[i]=ag[i];
 return 1;
}
__declspec(dllexport) int nfs_visibility_object_callback_apply(const NFVisibilityObjectCollector*c,uint8_t*objects,unsigned index,unsigned selector,const NFVisibilityObjectDelta*deltas,unsigned count){
 if(!c||!objects||c->awaiting_callback!=1||c->cursor.count>512||index!=c->cursor.current||index>=c->cursor.count||selector!=half(objects+index*164+0x4e)||count>256||(count&&!deltas))return 0;
 for(unsigned i=0;i<count;i++){
  if(deltas[i].offset>=c->cursor.count*164u||deltas[i].before>255||deltas[i].after>255||objects[deltas[i].offset]!=deltas[i].before)return 0;
  for(unsigned j=0;j<i;j++)if(deltas[j].offset==deltas[i].offset)return 0;
 }
 for(unsigned i=0;i<count;i++)objects[deltas[i].offset]=(uint8_t)deltas[i].after;
 return 1;
}
__declspec(dllexport) int nfs_visibility_object_collect_step(NFVisibilityObjectCollector*c,uint8_t*objects,uint8_t*visited,size_t visited_bytes,const uint32_t matrix[12],uint32_t*head,uint32_t*maximum,uint32_t*callback){
 if(!c||!objects||!visited||!matrix||!head||!maximum||!callback||c->cursor.count>512||c->awaiting_callback>1)return -1;
 unsigned index=c->cursor.current;
 if(index==65535)return c->awaiting_callback?-1:0;
 if(index>=c->cursor.count)return -1;
 uint8_t*object=objects+index*164;int active=1;
 if(!c->awaiting_callback){
  active=nfs_visibility_object_visit(visited,visited_bytes,index,object,callback);
  if(active<0)return -1;
  if(active&&(half(object+8)&3)==1){c->awaiting_callback=1;return 2;}
 }
 NFVisibilityObjectCursor next=c->cursor;
 if(nfs_visibility_object_cursor_advance(&next,object)<0)return -1;
 if(active&&nfs_visibility_object_sort(objects,c->cursor.count,index,matrix,head,maximum)<0)return -1;
 c->cursor=next;c->awaiting_callback=0;*callback=65535;return 1;
}
__declspec(dllexport) int nfs_visibility_object_cursor_begin(NFVisibilityObjectCursor*cursor,unsigned head,unsigned count){
 if(!cursor||count>512||(head!=65535&&head>=count))return -1;
 NFVisibilityObjectCursor result={0};result.current=head;result.count=count;
 if(head!=65535)result.seen[head]=1;
 *cursor=result;return head==65535?0:1;
}
__declspec(dllexport) int nfs_visibility_object_cursor_advance(NFVisibilityObjectCursor*cursor,const uint8_t object[164]){
 if(!cursor||cursor->count>512)return -1;
 if(cursor->current==65535)return 0;
 if(!object||cursor->current>=cursor->count)return -1;
 unsigned next=half(object+2);
 if(next!=65535&&(next>=cursor->count||cursor->seen[next]))return -1;
 cursor->current=next;if(next!=65535)cursor->seen[next]=1;
 return next==65535?0:1;
}
__declspec(dllexport) int nfs_visibility_object_visit(uint8_t*visited,size_t visited_bytes,unsigned index,const uint8_t object[164],uint32_t*callback){
 if(!visited||!object||!callback||index>=512||index/8>=visited_bytes)return -1;
 unsigned bit=1u<<(index&7);*callback=65535;
 if(visited[index/8]&bit)return 0;
 visited[index/8]|=(uint8_t)bit;
 if(!half(object+0x48))return 0;
 unsigned flags=half(object+8);
 if((flags&3)==1)*callback=half(object+0x4e);
 return 1;
}
__declspec(dllexport) int nfs_visibility_object_insert(uint8_t*objects,unsigned count,unsigned candidate,uint32_t*head,uint32_t*maximum){
 if(!objects||!head||!maximum||!count||count>512||candidate>=count||half(objects+candidate*164)!=candidate)return 0;
 unsigned node=*head,steps=0;uint8_t seen[512]={0};
 while(node!=65535){if(node>=count||node==candidate||seen[node]||++steps>count)return 0;seen[node]=1;node=half(objects+node*164+4);}
 uint8_t*item=objects+candidate*164;uint32_t distance=word(item+0x28);
 if((int32_t)distance>=(int32_t)*maximum){put(item+4,(uint16_t)*head);*head=candidate;*maximum=distance;return 1;}
 if(*head==65535)return 0;
 unsigned previous=*head;node=half(objects+previous*164+4);
 while(node!=65535&&(int32_t)word(objects+node*164+0x28)>(int32_t)distance){previous=node;node=half(objects+node*164+4);}
 put(item+4,(uint16_t)node);put(objects+previous*164+4,(uint16_t)candidate);return 1;
}
__declspec(dllexport) int nfs_visibility_object_distance(const uint32_t matrix[12],const uint8_t object[164],uint32_t out[3]){
 if(!matrix||!object||!out)return 0;
 uint32_t x=matrix[9]+sar(word(object+12),8),z=matrix[11]+sar(word(object+20),8);
 uint32_t cx=sar(matrix[0]*x+matrix[6]*z,14),cz=sar(matrix[2]*x+matrix[8]*z,14);
 uint32_t result[3]={cx,cz,sar(cx*cx+cz*cz,8)};memcpy(out,result,12);return 1;
}
__declspec(dllexport) int nfs_visibility_object_sort(uint8_t*objects,unsigned count,unsigned candidate,const uint32_t matrix[12],uint32_t*head,uint32_t*maximum){
 if(!objects||!matrix||!head||!maximum||count>512||candidate>=count)return -1;
 uint8_t*item=objects+candidate*164;
 if(!(half(item+8)&4))return 0;
 uint32_t position[3],old=word(item+0x28);
 nfs_visibility_object_distance(matrix,item,position);memcpy(item+0x28,position+2,4);
 if((int32_t)position[1]<=0)return 0;
 if(nfs_visibility_object_insert(objects,count,candidate,head,maximum))return 1;
 memcpy(item+0x28,&old,4);return -1;
}
__declspec(dllexport) int nfs_visibility_object_draw_setup(uint8_t state[256],const uint8_t record[16],const uint8_t object[164],const uint32_t matrix[12],uint32_t xyz[3]){
 if(!state||!record||!object||!matrix||!xyz)return 0;
 uint32_t planar[3];nfs_visibility_object_distance(matrix,object,planar);
 uint32_t result[3]={planar[0],matrix[10]+sar(word(object+16),8),planar[1]};
 memcpy(state+0xe2,record+2,4);memcpy(xyz,result,12);return 1;
}
__declspec(dllexport) int nfs_visibility_object_sorted_plan(const uint8_t*objects,unsigned count,unsigned head,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(!objects||!out||!out_count||count>512)return 0;
 uint32_t staged[512];uint8_t seen[512]={0};unsigned n=0,node=head;
 while(node!=65535){
  if(node>=count||seen[node]||n>=capacity)return 0;
  seen[node]=1;staged[n++]=node;node=half(objects+node*164+4);
 }
 memcpy(out,staged,n*sizeof(*out));*out_count=n;return 1;
}
__declspec(dllexport) int nfs_visibility_object_region(const uint8_t state[256],const uint8_t object[164],uint8_t record[16]){
 if(!state||!object||!record)return -1;
 if(!(half(object+10)&16))return 0;
 if(half(object+0x36)>=512)return -1;
 uint8_t result[16];memcpy(result,record,16);put(result,half(object+0x36));memcpy(result+2,state+0xe2,8);
 put(result+10,0);put(result+12,0);put(result+14,65535);
 memcpy(record,result,16);return 1;
}
static uint32_t arm_lsl(uint32_t v,unsigned n){n&=255;return n<32?v<<n:0;}
static uint32_t surface_div(uint32_t v,uint32_t reciprocal){
 int64_t product=(int64_t)(int32_t)v*(int64_t)(int32_t)reciprocal;
 return (uint32_t)((uint64_t)product>>8);
}
__declspec(dllexport) int nfs_visibility_surface_vertices(const uint8_t scratch[52],const uint32_t heights[4],const uint32_t attributes[4],const uint32_t params[6],const uint32_t reciprocal[32768],uint8_t*out,size_t capacity,unsigned*out_count){
 if(!scratch||!heights||!attributes||!params||!reciprocal||!out||!out_count)return 0;
 unsigned count=(half(scratch+0x30)&8)?2:1;
 if(capacity<count*24u)return 0;
 int depths[2]={(int16_t)half(scratch+4),(int16_t)half(scratch+6)};
 if(depths[0]<=0||depths[1]<=0)return 0;
 uint8_t result[48];memcpy(result,out,count*24u);
 for(unsigned j=0;j<count;j++){
  unsigned i=2-count+j;uint32_t r=reciprocal[depths[i]],scale=sar(r*params[0],7);
  uint32_t x=params[1]+sar(sar((uint32_t)(int32_t)(int16_t)half(scratch+i*2),1)*scale,16);
  uint32_t values[6]={(uint32_t)(int32_t)(int16_t)x,
   params[2]+sar(sar(heights[i*2],1)*scale,16),params[2]+sar(sar(heights[i*2+1],1)*scale,16),r,0,0};
  uint32_t u=arm_lsl(attributes[i*2],params[3]),v=attributes[i*2+1]*params[4];
  if(params[5]){values[3]=word(result+j*24+12);values[4]=u<<1;values[5]=v<<1;}
  else{values[4]=surface_div(sar(u,7),r);values[5]=surface_div(sar(v,7),r);}
  memcpy(result+j*24,values,24);
 }
 memcpy(out,result,count*24u);*out_count=count;return 1;
}
__declspec(dllexport) int nfs_visibility_wall_project(uint8_t scratch[52],const uint32_t params[5],const uint32_t reciprocal[32768]){
 if(!scratch||!params||!reciprocal)return 0;
 int z0=(int16_t)half(scratch+4),z1=(int16_t)half(scratch+6);
 if(z0<=0||z1<=0)return 0;
 uint8_t result[52];memcpy(result,scratch,52);
 uint32_t scales[2]={sar(reciprocal[z0]*params[0],7),sar(reciprocal[z1]*params[0],7)};
 for(unsigned i=0;i<2;i++){
  uint32_t x=sar((uint32_t)(int32_t)(int16_t)half(scratch+i*2),1);
  put(result+i*2,(uint16_t)(params[1]+sar(x*scales[i],16)));
 }
 unsigned flags=half(scratch+0x30);
 if((flags&0x2000)&&(int16_t)half(result+2)<(int16_t)half(result))flags|=2;
 if(flags&2){uint16_t x=half(result);put(result,half(result+2));put(result+2,x);}
 int32_t left=(int16_t)half(result),right=(int16_t)half(result+2);
 if(right<=left||right<(int32_t)params[3]||left>=(int32_t)params[4])flags|=4;
 else for(unsigned i=0;i<4;i++){
  uint32_t y=sar((uint32_t)(int32_t)(int16_t)half(scratch+8+i*2),1);
  put(result+8+i*2,(uint16_t)(params[2]+sar(y*scales[i&1],16)));
 }
 put(result+0x30,(uint16_t)flags);memcpy(scratch,result,52);return 1;
}
/* Signed word times unsigned fixed24 factor, retaining original low word. */
static uint32_t wall_scale(uint32_t value,uint32_t factor){
 int64_t product=(int64_t)(int32_t)value*(int64_t)factor;
 return (uint32_t)((uint64_t)product>>24);
}
__declspec(dllexport) int nfs_visibility_wall_clip(uint8_t scratch[52],uint32_t heights[4],uint32_t attributes[4],int near_depth,unsigned source_flags,unsigned region_flags,const uint32_t reciprocal[32768]){
 if(!scratch||!heights||!attributes||!reciprocal||near_depth<0||near_depth>32767)return -1;
 int z0=(int16_t)half(scratch+4),z1=(int16_t)half(scratch+6);
 if(z0<near_depth&&z1<near_depth)return 0;
 if(z0>=near_depth&&z1>=near_depth)return 1;
 unsigned start=z0<near_depth,delta=(unsigned)(start?z1-z0:z0-z1);
 if(delta>=32768)return -1;
 uint32_t factor=(uint32_t)(near_depth-(start?z0:z1))*reciprocal[delta];
 uint8_t result[52];uint32_t h[4],a[4];memcpy(result,scratch,52);memcpy(h,heights,16);memcpy(a,attributes,16);
 const unsigned pairs[4][2]={{0,2},{0x28,0x2a},{8,10},{12,14}};
 for(unsigned i=0;i<4;i++){
  unsigned x=pairs[i][0],y=pairs[i][1],target=start?x:y;
  uint32_t d=(uint32_t)(int32_t)(int16_t)half(scratch+y)-(uint32_t)(int32_t)(int16_t)half(scratch+x);
  uint32_t adjustment=wall_scale(d,factor);
  put(result+target,(uint16_t)(half(scratch+target)+(start?adjustment:0u-adjustment)));
 }
 const unsigned uv[3][2]={{0x10,0x14},{0x18,0x20},{0x1c,0x24}};
 for(unsigned i=0;i<((source_flags&0x80)?3u:1u);i++){
  unsigned x=uv[i][0],y=uv[i][1],target=start?x:y;
  uint32_t adjustment=wall_scale(word(scratch+y)-word(scratch+x),factor);
  uint32_t value=word(scratch+target)+(start?adjustment:0u-adjustment);memcpy(result+target,&value,4);
 }
 for(unsigned i=0;i<2;i++){
  unsigned target=start?i:i+2;
  uint32_t adjustment=wall_scale(a[i+2]-a[i],factor);
  a[target]+=start?adjustment:0u-adjustment;
  if(region_flags){adjustment=wall_scale(h[i+2]-h[i],factor);h[target]+=start?adjustment:0u-adjustment;}
 }
 put(result+(start?4:6),(uint16_t)near_depth);put(result+0x30,(uint16_t)(half(result+0x30)|(start?8:16)));
 memcpy(scratch,result,52);memcpy(heights,h,16);memcpy(attributes,a,16);return 1;
}
__declspec(dllexport) int nfs_visibility_wall_uv(const uint8_t source[68],const uint8_t material[32],uint32_t u_base,uint32_t v_offset,uint32_t u_extent,uint8_t scratch[52]){
 if(!source||!material||!scratch)return 0;
 uint8_t result[52];memcpy(result,scratch,52);
 unsigned flags=half(source+0x2e),shift=(half(material+0x1a)-1u)&255u;
 uint32_t end=u_base+(shift<32?u_extent<<shift:0u);
 uint32_t uv[6]={(flags&2)?end:u_base,(flags&2)?u_base:end,
  word(source+0x10)+v_offset,word(source+0x18)+v_offset,
  word(source+0x14)+v_offset,word(source+0x1c)+v_offset};
 memcpy(result+0x10,uv,sizeof(uv));put(result+0x30,(uint16_t)flags);
 memcpy(scratch,result,52);return 1;
}
__declspec(dllexport) int nfs_visibility_draw_plan(const uint8_t queue[NF_VISIBILITY_QUEUE_BYTES],unsigned count,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(!queue||!out||!out_count||count>NF_VISIBILITY_QUEUE_CAPACITY)return 0;
 uint32_t plan[4*NF_VISIBILITY_QUEUE_CAPACITY];unsigned n=0;
 for(unsigned pass=0;pass<2;pass++)for(unsigned i=count;i>0;i--){
  unsigned flags=half(queue+(i-1)*16+10);
  if(flags&(pass?0x88:8))continue;
  plan[n*2]=i-1;plan[n*2+1]=pass;n++;
 }
 if(n>capacity)return 0;
 memcpy(out,plan,n*2*sizeof(uint32_t));*out_count=n;return 1;
}
static uint32_t visibility_sine(uint32_t angle,const int16_t*table){
 angle&=0x3fff;uint32_t value=(uint32_t)(int32_t)table[angle&0x1fff];return angle>0x1fff?0u-value:value;
}
__declspec(dllexport) int nfs_visibility_view_matrix(uint32_t angle,const uint32_t position[3],const int16_t table[8192],uint32_t out[12]){
 if(!position||!table||!out)return 0;
 uint32_t sine=visibility_sine(angle,table),cosine=visibility_sine(angle+0x1000u,table);
 uint32_t matrix[12]={cosine,0,0u-sine,0,0x4000,0,sine,0,cosine,0u-position[0],0u-position[1],0u-position[2]};
 memcpy(out,matrix,sizeof(matrix));return 1;
}
/* ROM seed at 08615F08, Thumb 08002CF2..08002D06 / 0806DEC0. */
__declspec(dllexport) int nfs_visibility_offset(const uint32_t matrix[12],uint32_t out[3]){
 if(!matrix||!out)return 0;
 uint32_t result[3];
 for(unsigned i=0;i<3;i++)result[i]=sar(matrix[i]*8u+matrix[i+6]*80u,14)+matrix[i+9];
 memcpy(out,result,sizeof(result));return 1;
}
/* Original 03004BF4: oriented half-plane test over 68-byte world records.
   Preserve 32-bit ARM cross-product wrap and accept points on boundaries. */
__declspec(dllexport) int nfs_visibility_contains(const uint8_t*vertices,size_t bytes,unsigned count,uint32_t x,uint32_t z,unsigned descriptor,uint32_t*out){
 if(!out||count>32||descriptor>=512||(count&&(!vertices||bytes<(size_t)count*68)))return 0;
 uint32_t result=descriptor;
 for(unsigned i=0;i<count;i++){
  const uint8_t*a=vertices+((i?i:count)-1)*68,*b=vertices+i*68;
  uint32_t ax=word(a),az=word(a+4);
  uint32_t cross=(word(b+4)-az)*(x-ax)-(z-az)*(word(b)-ax);
  if(cross&0x80000000u){result=65535;break;}
 }
 *out=result;return 1;
}
/* 03002C80..03002D20 planar world edge transform. points=x0,z0,x1,z1;
   matrix is the original 12-word camera matrix. Preserve ARM multiply/add
   wrapping before the fixed14 shift. Ring endpoint selection is the caller's
   responsibility; output is x0,z0,x1,z1 in camera space. */
__declspec(dllexport) int nfs_visibility_transform(const uint32_t points[4],const uint32_t matrix[12],uint32_t out[4]){
 if(!points||!matrix||!out)return 0;
 uint32_t result[4];
 for(unsigned i=0;i<2;i++){
  uint32_t x=points[i*2]+matrix[9],z=points[i*2+1]+matrix[11];
  result[i*2]=sar(x*matrix[0]+z*matrix[6],14);
  result[i*2+1]=sar(x*matrix[2]+z*matrix[8],14);
 }
 memcpy(out,result,sizeof(result));return 1;
}
/* Original 03002D20..03002E18. p=x0,z0,x1,z1,near,center,scale,sort.
   out=projected left/right,clipped z0/z1,endpoint flags. Return 1 projected,
   0 both behind near plane, 2 original far-depth traversal stop, -1 invalid.
   Reproduce fixed-point wrap; this is a reference visibility stage, not a
   substitute for continuous world geometry in the native high-res renderer. */
__declspec(dllexport) int nfs_visibility_project(const int32_t p[8],const uint32_t*reciprocal,uint32_t out[5]){
 if(!p||!reciprocal||!out||p[4]<=0||p[4]>0x6000||p[5]<-32768||p[5]>32767)return -1;
 uint32_t x0=(uint32_t)p[0],x1=(uint32_t)p[2];int32_t z0=p[1],z1=p[3],near=p[4];unsigned flags=0;
 if(z0>0x6000||z1>0x6000)return 2;
 if(z0<near&&z1<near)return 0;
 if(z0<near||z1<near){
  int64_t difference=z0<near?(int64_t)z1-z0:(int64_t)z0-z1;
  if(difference<=0||difference>=32768)return -1;
  uint32_t distance=(uint32_t)near-(uint32_t)(z0<near?z0:z1);
  uint32_t numerator=distance*(x1-x0);
  uint32_t delta=(uint32_t)((uint64_t)((int64_t)(int32_t)numerator*(int64_t)(int32_t)reciprocal[difference])>>24);
  if(z0<near){x0+=delta;z0=near;flags=8;}else{x1-=delta;z1=near;flags=16;}
 }
 uint32_t a=(uint32_t)p[6]*reciprocal[z0],b=(uint32_t)p[6]*reciprocal[z1];
 uint32_t left=(uint32_t)p[5]+sar(sar(a,7)*sar(x0,1),16);
 uint32_t right=(uint32_t)p[5]+sar(sar(b,7)*sar(x1,1),16);
 if(p[7]&&(int32_t)left>(int32_t)right){uint32_t temp=left;left=right;right=temp;}
 out[0]=left;out[1]=right;out[2]=(uint32_t)z0;out[3]=(uint32_t)z1;out[4]=flags;return 1;
}
/* 03002F14..03002F60 membership insertion, restricted to representable groups.
   Original overflow can leave an unusable membership count; reject that case
   atomically instead. Call after a candidate record has been constructed. */
__declspec(dllexport) int nfs_visibility_insert(uint8_t*groups,unsigned group_count,unsigned descriptor,unsigned capacity,uint32_t*next,uint32_t*total){
 if(!groups||!next||!total||group_count>512||descriptor>=group_count||capacity>NF_VISIBILITY_QUEUE_CAPACITY||*next>=capacity)return 0;
 uint8_t*group=groups+descriptor*8;unsigned members=group[0];
 if(members>=7)return 0;
 group[0]=(uint8_t)(members+1);group[members+1]=(uint8_t)*next;
 (*next)++;(*total)++;return 1;
}
/* 03002E18..03002F14: candidate gate and record construction, after camera
   transform/near clipping/projection. p: left,right,z0,z1,clip flags,material
   flags,descriptor,viewport left/right,top/bottom. Return -1 invalid, 0 culled,
   1 accepted. Original +E record bytes remain untouched. */
__declspec(dllexport) int nfs_visibility_edge_record(const uint8_t*source,const int32_t p[11],uint8_t*out){
 if(!source||!p||!out)return -1;
 for(unsigned i=6;i<11;i++)if(p[i]<0||p[i]>65535)return -1;
 int32_t left=p[0],right=p[1];
 if(left>=right||right<p[7]||left>=p[8])return 0;
 uint8_t record[16];memcpy(record,out,16);
 unsigned flags=half(source+10)&0x80;
 if((uint32_t)p[5]&0x800)flags=0x80;
 int32_t source_left=(int16_t)half(source+2),source_right=(int16_t)half(source+4);
 put(record+2,((uint32_t)p[4]&8)?2:(uint16_t)(left<source_left?source_left:left));
 put(record+4,((uint32_t)p[4]&16)?238:(uint16_t)(right>source_right?source_right:right));
 put(record,(uint16_t)p[6]);put(record+6,(uint16_t)p[9]);put(record+8,(uint16_t)p[10]);
 put(record+12,(uint16_t)(half(source+12)+1));
 if((p[2]<p[3]?p[2]:p[3])>0x800)flags|=1;
 put(record+10,(uint16_t)flags);memcpy(out,record,16);return 1;
}
/* Original 0300556C linked descriptor append. The caller supplies the current
   viewport's horizontal bounds; vertical bounds and depth come from source.
   Queue capacity is enforced before publishing either bytes or counters. */
__declspec(dllexport) int nfs_visibility_append(uint8_t*queue,unsigned capacity,uint32_t*next,uint32_t*total,uint32_t*linked,const uint8_t*source,unsigned descriptor,unsigned left,unsigned right){
 if(!queue||!next||!total||!linked||!source||capacity>NF_VISIBILITY_QUEUE_CAPACITY||*next>capacity||descriptor>65535||left>65535||right>65535)return 0;
 if(descriptor==65535)return 1;
 if(*next==capacity)return 0;
 uint8_t record[16];memcpy(record,source,16);
 put(record,descriptor);put(record+2,left);put(record+4,right);
 put(record+10,0x80);put(record+14,half(source));
 memcpy(queue+*next*16,record,16);(*next)++;(*total)++;(*linked)++;
 return 1;
}
/* Original 03005620: merge horizontal bounds of repeated descriptor visits.
   Each 8-byte group is a count followed by at most seven queue indices.
   Preserve the first member, mark subsequent members with flag 8. Work on a
   private copy so malformed membership data cannot partially alter a queue.
   This is one builder stage, not complete world visibility or motion code. */
__declspec(dllexport) int nfs_visibility_merge(uint8_t*queue,unsigned count,const uint8_t*groups,unsigned group_count){
 if(count>NF_VISIBILITY_QUEUE_CAPACITY||group_count>512||(count&&(!queue||!groups)))return 0;
 uint8_t copy[NF_VISIBILITY_QUEUE_BYTES];if(count)memcpy(copy,queue,count*16);
 for(unsigned i=0;i<count;i++){
  uint8_t*entry=copy+i*16;
  if(half(entry+10)&8)continue;
  unsigned descriptor=half(entry);if(descriptor>=group_count)return 0;
  const uint8_t*group=groups+descriptor*8;unsigned members=group[0];
  if(members>7)return 0;
  if(members<=1)continue;
  unsigned first=group[1];if(first>=count)return 0;
  uint8_t*target=copy+first*16;int16_t left=(int16_t)half(target+2),right=(int16_t)half(target+4);
  for(unsigned j=1;j<members;j++){
   unsigned index=group[j+1];if(index>=count)return 0;
   uint8_t*other=copy+index*16;int16_t a=(int16_t)half(other+2),b=(int16_t)half(other+4);
   if(a<left)left=a;
   if(b>=right)right=b;
   put(other+10,half(other+10)|8);
  }
  put(target+2,(uint16_t)left);put(target+4,(uint16_t)right);
 }
 if(count)memcpy(queue,copy,count*16);
 return 1;
}
/* Complete 03002B74 traversal over one bounded geometry ring. Inputs are
   retained data, never pointers into running emulator memory. All mutable
   outputs publish together only on success. Original capacity overflow is
   rejected rather than writing beyond the queue or membership table. */
__declspec(dllexport) int nfs_visibility_traverse(uint8_t*state,const uint8_t*descriptor,const uint8_t*vertices,unsigned vertex_bytes,const uint32_t*camera,const uint8_t*projection,const uint8_t*parent,const uint32_t*reciprocal,uint8_t*queue,uint8_t*groups,uint32_t*next,uint32_t*total,unsigned sort){
 if(!state||!descriptor||!vertices||!camera||!projection||!parent||!reciprocal||!queue||!groups||!next||!total||*next>NF_VISIBILITY_QUEUE_CAPACITY){visibility_failure_stage=100;return /* diagnostic */ 0;}
 unsigned count=half(descriptor+2);if(count>32||vertex_bytes<count*68){visibility_failure_stage=101;return /* diagnostic */ 0;}
 uint8_t s[256],q[NF_VISIBILITY_QUEUE_BYTES],g[4096],source[16];memcpy(s,state,256);memcpy(q,queue,NF_VISIBILITY_QUEUE_BYTES);memcpy(g,groups,4096);memcpy(source,parent,16);
 uint32_t n=*next,t=*total;
 if(!half(descriptor+4))put(s+0xf6,1);
 memcpy(s+0xe2,source+2,8);
 for(unsigned i=0;i<count;i++){
  const uint8_t*a=vertices+i*68,*b=vertices+((i+1)%count)*68;
  unsigned target=half(a+0x30);if(target==65535)continue;
  uint32_t points[4]={word(a),word(a+4),word(b),word(b+4)},camera_edge[4],projected[5];
  if(!nfs_visibility_transform(points,camera,camera_edge)){visibility_failure_stage=102;return /* diagnostic */ 0;}
  int32_t p[8]={(int32_t)camera_edge[0],(int32_t)camera_edge[1],(int32_t)camera_edge[2],(int32_t)camera_edge[3],(int32_t)word(projection+16),(int16_t)half(projection+8),(int32_t)word(projection+28),sort!=0};
  int result=nfs_visibility_project(p,reciprocal,projected);
  if(result<0){visibility_failure_stage=103;return /* diagnostic */ 0;}
  if(result==2)break;
  if(!result)continue;
  int32_t e[11]={(int32_t)projected[0],(int32_t)projected[1],(int32_t)projected[2],(int32_t)projected[3],(int32_t)projected[4],half(a+0x2e),target,half(s+0xe2),half(s+0xe4),half(s+0x5c),half(s+0x5e)};
  uint8_t record[16]={0};if(n<NF_VISIBILITY_QUEUE_CAPACITY)memcpy(record,q+n*16,16);
  result=nfs_visibility_edge_record(source,e,record);if(result<0){visibility_failure_stage=104;return /* diagnostic */ 0;}
  if(result){
   uint32_t index=n;if(!nfs_visibility_insert(g,512,target,NF_VISIBILITY_QUEUE_CAPACITY,&n,&t)){visibility_failure_stage=n>=NF_VISIBILITY_QUEUE_CAPACITY?106:(target>=512?108:(g[target*8]>=7?107:105));return /* diagnostic */ 0;}
   memcpy(q+index*16,record,16);
  }
 }
 memcpy(state,s,256);memcpy(queue,q,NF_VISIBILITY_QUEUE_BYTES);memcpy(groups,g,4096);*next=n;*total=t;return 1;
}
static int indexed_read(NFVisibilityRead read,void*context,uint32_t base,unsigned index,unsigned stride,void*out,size_t size){
 uint64_t address=(uint64_t)base+(uint64_t)index*stride;
 if(address>UINT32_MAX||size>UINT32_MAX-address)return 0;
 return read(context,(uint32_t)address,out,size);
}
__declspec(dllexport) int nfs_visibility_region_links(const uint8_t state[256],const uint8_t descriptor[48],NFVisibilityRead read,void*context,uint32_t*out,unsigned capacity,unsigned*out_count,unsigned*replaces_self){
 if(!state||!descriptor||!read||!out||!out_count||!replaces_self)return 0;
 unsigned replace=(descriptor[0x12]&8)!=0,index=half(descriptor+(replace?0x24:6)),count=0;uint32_t children[512];uint8_t seen[512]={0},child[48];
 while(index!=65535){
  if(index>=512||seen[index]||count>=capacity)return 0;
  seen[index]=1;children[count++]=index;
  if(!replace)break;
  if(!indexed_read(read,context,word(state+0x14),index,48,child,48))return 0;
  index=half(child+0x24);
 }
 memcpy(out,children,count*4u);*out_count=count;*replaces_self=replace;return 1;
}
__declspec(dllexport) int nfs_visibility_wall_draw_plan(const uint8_t state[256],const uint8_t*vertices,unsigned count,const uint8_t*scratch,uint32_t second_pass,NFVisibilityRead read,void*context,NFVisibilityWallDraw*out,unsigned capacity,unsigned*out_count,uint32_t*deferred){
 if(!state||!vertices||!scratch||!read||!out||!out_count||!deferred||count>32)return 0;
 NFVisibilityWallDraw plan[32];unsigned n=0;uint32_t mask=0;
 for(unsigned i=0;i<count;i++){
  const uint8_t*v=vertices+i*68,*edge=scratch+i*52;uint8_t material[32],animation[8];
  unsigned flags=half(edge+0x30),source_flags=half(v+0x2e),index=half(v+0x2a),hidden=source_flags&1,remaining=count-i;
  if(index!=65535){if(!indexed_read(read,context,word(state+0x18),index,32,material,32))return 0;hidden=half(material+0xe)&1;}
  if(hidden)continue;
  if(!second_pass){if(flags&4)continue;if(flags&2){mask|=arm_lsl(1,remaining);continue;}}
  else if(!((remaining>=32?sar(second_pass,31):sar(second_pass,remaining))&1))continue;
  if((int16_t)half(edge+8)>=half(state+0xe8)&&(int16_t)half(edge+10)>=half(state+0xe8)&&
     (int16_t)half(edge+12)<half(state+0xe6)&&(int16_t)half(edge+14)<half(state+0xe6))continue;
  index=half(v+0x2c);
  if(!indexed_read(read,context,word(state+0x20),index,32,material,32))return 0;
  unsigned anim=half(material);if(!anim)continue;
  if(!indexed_read(read,context,word(state+0x48),anim,8,animation,8))return 0;
  uint64_t address=(uint64_t)word(state+0x20)+(uint64_t)(index+half(animation+2))*32;
  if(address>UINT32_MAX||!read(context,(uint32_t)address,material,32))return 0;
  plan[n++]=(NFVisibilityWallDraw){i,(uint32_t)address,word(state)+word(material+4),half(material+0x1a),half(material+0xa),source_flags};
 }
 if(n>capacity)return 0;
 memcpy(out,plan,n*sizeof(*out));*out_count=n;*deferred=mask;return 1;
}
__declspec(dllexport) int nfs_visibility_wall_prepare(const uint8_t state[256],const uint8_t source[68],const uint8_t next[68],const uint32_t bases[2],NFVisibilityRead read,void*context,uint32_t heights[4],uint8_t scratch[52]){
 if(!state||!source||!next||!bases||!read||!heights||!scratch)return 0;
 uint8_t material[32],animation[8],offset[32],result[52];uint32_t h[4];
 if(!indexed_read(read,context,word(state+0x20),half(source+0x2c),32,material,32)||
    !indexed_read(read,context,word(state+0x48),half(material),8,animation,8))return 0;
 const uint8_t*vertices[2]={source,next};
 for(unsigned i=0;i<2;i++){
  h[i*2]=bases[0]+(uint32_t)(int32_t)(int16_t)half(vertices[i]+0x38);
  h[i*2+1]=bases[1]+(uint32_t)(int32_t)(int16_t)half(vertices[i]+0x3a);
  unsigned index=half(vertices[i]+0x2a);
  if(index!=65535){
   if(!indexed_read(read,context,word(state+0x18),index,32,offset,32))return 0;
   h[i*2]+=(uint32_t)(int32_t)(int16_t)half(offset+6);
   h[i*2+1]+=(uint32_t)(int32_t)(int16_t)half(offset+4);
  }
 }
 uint32_t ub=((uint32_t)half(source+0x28)<<7)+sar((uint32_t)(int32_t)(int16_t)half(animation+4),1);
 uint32_t vo=sar((uint32_t)(int32_t)(int16_t)half(animation+6),1);
 memcpy(result,scratch,52);nfs_visibility_wall_uv(source,material,ub,vo,half(source+0x40),result);
 memcpy(heights,h,sizeof(h));memcpy(scratch,result,52);return 1;
}
static int region_output(const uint8_t state[256],const uint8_t descriptor[48],const uint8_t*vertices,unsigned count,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes,uint8_t*surface,size_t surface_bytes,unsigned*surface_count,unsigned queue_flags){
 if(!state||!descriptor||!vertices||!read||!reciprocal||!scratch||count>32||scratch_bytes<count*52u)return 0;
 if(!count){if(surface_count)*surface_count=0;return 1;}
 uint8_t projection[32],matrix[48],material[20],result[32*52];
 if(!read(context,word(state+0x50),projection,32)||!read(context,word(state+0x54),matrix,48))return 0;
 uint32_t bases[2]={word(matrix+0x28),word(matrix+0x28)};
 unsigned index=half(descriptor+0xa);
 if(index!=65535){
  if(!indexed_read(read,context,word(state+0x1c),index,20,material,20))return 0;
  bases[0]+=(uint32_t)(int32_t)(int16_t)half(material+6);
  bases[1]+=(uint32_t)(int32_t)(int16_t)half(material+4);
 }
 uint32_t params[5]={word(projection+0x1c),(uint32_t)(int32_t)(int16_t)half(projection+8),(uint32_t)(int32_t)(int16_t)half(projection+10),half(state+0xe2),half(state+0xe4)};
 uint8_t stream[64*24],surface_material[32];unsigned emitted=0;
 int has_surface=surface&&(half(descriptor+8)||half(descriptor+4));
 size_t retained=surface_bytes<sizeof(stream)?surface_bytes:sizeof(stream);
 uint32_t surface_params[6]={params[0],params[1],params[2],0,0,queue_flags&1};
 if(has_surface){
  unsigned material_index=half(descriptor+8)?half(descriptor+8):half(descriptor+4);
  if(!indexed_read(read,context,word(state+0x20),material_index,32,surface_material,32))return 0;
  surface_params[3]=half(surface_material+0x1a);surface_params[4]=half(surface_material+0xa);
  memcpy(stream,surface,retained);
 }
 memcpy(result,scratch,count*52u);
 for(unsigned i=0;i<count;i++){
  const uint8_t*source=vertices+i*68,*next=vertices+((i+1)%count)*68;uint8_t*edge=result+i*52;
  uint32_t heights[4],attributes[4]={word(source+0x20),word(source+0x24),word(next+0x20),word(next+0x24)};
  if(!nfs_visibility_wall_prepare(state,source,next,bases,read,context,heights,edge))return 0;
  int visible=nfs_visibility_wall_clip(edge,heights,attributes,(int32_t)word(projection+0x10),half(source+0x2e),descriptor[0x12],reciprocal);
  if(visible<0)return 0;
  if(!visible)put(edge+0x30,(uint16_t)(half(edge+0x30)|0x24));
  else {
   if(has_surface){unsigned added=0;
    if(!nfs_visibility_surface_vertices(edge,heights,attributes,surface_params,reciprocal,stream+emitted*24,retained-emitted*24,&added))return 0;
    emitted+=added;
   }
   if(!nfs_visibility_wall_project(edge,params,reciprocal))return 0;
  }
 }
 memcpy(scratch,result,count*52u);
 if(surface_count){if(emitted)memcpy(surface,stream,emitted*24);*surface_count=emitted;}
 return 1;
}
__declspec(dllexport) int nfs_visibility_region_walls(const uint8_t state[256],const uint8_t descriptor[48],const uint8_t*vertices,unsigned count,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes){
 return region_output(state,descriptor,vertices,count,read,context,reciprocal,scratch,scratch_bytes,0,0,0,0);
}
__declspec(dllexport) int nfs_visibility_region_geometry(uint8_t state[256],const uint8_t descriptor[48],const uint8_t*vertices,unsigned count,unsigned queue_flags,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes,uint8_t*surface,size_t surface_bytes){
 if(!state||!surface)return 0;
 unsigned emitted;
 if(!region_output(state,descriptor,vertices,count,read,context,reciprocal,scratch,scratch_bytes,surface,surface_bytes,&emitted,queue_flags))return 0;
 put(state+0xf2,(uint16_t)emitted);return 1;
}
__declspec(dllexport) int nfs_visibility_region_reconstruct(uint8_t state[256],const uint8_t record[16],NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes,uint8_t*surface,size_t surface_bytes){
 if(!state||!record||!read||!reciprocal||!scratch||!surface)return -1;
 uint8_t s[256],descriptor[48],viewport[16],vertices[32*68],edges[32*52],stream[64*24];uint32_t geometry[2];
 memcpy(s,state,256);
 int status=nfs_visibility_region_setup(s,record,read,context,viewport,descriptor,geometry);
 if(status!=1)return status;
 size_t edge_bytes=geometry[1]*52u,stream_bytes=surface_bytes<sizeof(stream)?surface_bytes:sizeof(stream);
 if(scratch_bytes<edge_bytes||!read(context,geometry[0],vertices,geometry[1]*68u))return -1;
 memcpy(edges,scratch,edge_bytes);memcpy(stream,surface,stream_bytes);
 status=nfs_visibility_region_transform(s,vertices,geometry[1]*68u,geometry[1],read,context,edges,edge_bytes);
 if(status!=1)return status;
 if(!nfs_visibility_region_geometry(s,descriptor,vertices,geometry[1],half(record+10),read,context,reciprocal,edges,edge_bytes,stream,stream_bytes))return -1;
 memcpy(state,s,256);memcpy(scratch,edges,edge_bytes);memcpy(surface,stream,stream_bytes);return 1;
}
__declspec(dllexport) int nfs_visibility_region_setup(uint8_t*state,const uint8_t record[16],NFVisibilityRead read,void*context,uint8_t viewport[16],uint8_t descriptor[48],uint32_t geometry[2]){
 if(!state||!record||!read||!viewport||!descriptor||!geometry)return -1;
 unsigned index=half(record);uint8_t d[48],material[20],s[256];uint32_t bounds[4];
 if(index>=512||!indexed_read(read,context,word(state+0x14),index,48,d,48))return -1;
 unsigned mat=half(d+10);
 if(mat!=65535){if(!indexed_read(read,context,word(state+0x1c),mat,20,material,20))return -1;if(half(material+8)&0x40)return 0;}
 uint64_t address=(uint64_t)word(state+0x10)+(uint64_t)half(d)*68;
 if(address>UINT32_MAX||half(d+2)>32)return -1;
 memcpy(s,state,256);
 for(unsigned i=0;i<4;i++){uint16_t value=half(record+2+i*2);put(s+0xe2+i*2,value);bounds[i]=(uint32_t)(int32_t)(int16_t)value;}
 /* Record order is left,right,top,bottom; viewport is left,top,right,bottom. */
 uint32_t swap=bounds[1];bounds[1]=bounds[2];bounds[2]=swap;
 memcpy(state,s,256);memcpy(viewport,bounds,16);memcpy(descriptor,d,48);geometry[0]=(uint32_t)address;geometry[1]=half(d+2);return 1;
}
static int region_read(const uint8_t*state,unsigned index,NFVisibilityRead read,void*context,uint8_t descriptor[48],uint8_t vertices[32*68]){
 if(index>=512||!indexed_read(read,context,word(state+0x14),index,48,descriptor,48))return 0;
 unsigned count=half(descriptor+2);
 if(count>32)return 0;
 return !count||indexed_read(read,context,word(state+0x10),half(descriptor),68,vertices,count*68);
}
__declspec(dllexport) int nfs_visibility_region_transform(const uint8_t*state,const uint8_t*vertices,size_t vertex_bytes,unsigned count,NFVisibilityRead read,void*context,uint8_t*scratch,size_t scratch_bytes){
 if(!state||!vertices||!read||!scratch||count>32||vertex_bytes<(size_t)count*68||scratch_bytes<(size_t)count*52)return -1;
 uint32_t m[12];uint8_t result[32*52],material[32];
 if(!read(context,word(state+0x54),m,48))return -1;
 memcpy(result,scratch,count*52);
 for(unsigned i=0;i<count;i++){
  const uint8_t*v=vertices+i*68;uint8_t*out=result+i*52;unsigned mat=half(v+0x2a);
  uint32_t x=word(v)+m[9],z=word(v+4)+m[11],top=m[10],bottom=m[10];
  if(mat!=65535){
   if(!indexed_read(read,context,word(state+0x18),mat,32,material,32))return -1;
   x+=(uint32_t)(int32_t)(int16_t)half(material);z+=(uint32_t)(int32_t)(int16_t)half(material+2);
   top+=(uint32_t)(int32_t)(int16_t)half(material+8);bottom+=(uint32_t)(int32_t)(int16_t)half(material+10);
  }
  uint32_t cx=sar(x*m[0]+z*m[6],14),cz=sar(x*m[2]+z*m[8],14);
  put(out,(uint16_t)cx);put(out+8,(uint16_t)(half(v+8)+top));put(out+12,(uint16_t)(half(v+10)+bottom));
  put(out+10,(uint16_t)(half(v+12)+top));put(out+14,(uint16_t)(half(v+14)+bottom));
  if((int32_t)cz>0x5fff){memcpy(scratch,result,count*52);return 0;}
  put(out+4,(uint16_t)cz);put(out+40,(uint16_t)(v[60]<<8));put(out+42,(uint16_t)(v[61]<<8));
 }
 for(unsigned i=0;i<count;i++){uint8_t*previous=result+((i?i:count)-1)*52;put(previous+2,half(result+i*52));put(previous+6,half(result+i*52+4));}
 memcpy(scratch,result,count*52);return 1;
}
/* Original 03000BD0: retain containing current region, otherwise scan its
   permitted neighbors in source order, with the original linked redirect. */
__declspec(dllexport) int nfs_visibility_select(const uint8_t*state,NFVisibilityRead read,void*context,uint32_t*out){
 if(!state||!read||!out)return 0;
 uint8_t descriptor[48],vertices[32*68],neighbor[48],ring[32*68],material[32];
 unsigned current=half(state+0xea);uint32_t result,x=word(state+0xc0),z=word(state+0xc8);
 if(!region_read(state,current,read,context,descriptor,vertices))return 0;
 unsigned count=half(descriptor+2);
 if(!nfs_visibility_contains(vertices,count*68,count,x,z,current,&result))return 0;
 if(result!=65535){*out=result;return 1;}
 for(unsigned i=0;i<count;i++){
  const uint8_t*edge=vertices+i*68;unsigned mat=half(edge+0x2a),flags=half(edge+0x2e),target=half(edge+0x32);
  if(mat!=65535){
   if(!indexed_read(read,context,word(state+0x18),mat,32,material,32))return 0;
   flags=half(material+0xe);
  }
  if(target==65535||(flags&0x1000))continue;
  if(!region_read(state,target,read,context,neighbor,ring))return 0;
  unsigned n=half(neighbor+2);
  if(!nfs_visibility_contains(ring,n*68,n,x,z,target,&result))return 0;
  if(result!=65535){
   unsigned link=half(neighbor+0x20);
   if(!half(neighbor+8)&&link!=65535){if(link>=512)return 0;result=link;}
   *out=result;return 1;
  }
 }
 *out=65535;return 1;
}
static int permitted_neighbor(const uint8_t*state,const uint8_t*edge,NFVisibilityRead read,void*context,unsigned*out){
 unsigned mat=half(edge+0x2a),flags=half(edge+0x2e);uint8_t material[32];
 if(mat!=65535){if(!indexed_read(read,context,word(state+0x18),mat,32,material,32))return 0;flags=half(material+0xe);}
 *out=(flags&0x1000)?65535:half(edge+0x32);return 1;
}
/* Original Thumb 08022D78: ordered two-hop search after local selection fails.
   Intermediate neighbors need not contain the point; only destinations do. */
__declspec(dllexport) int nfs_visibility_fallback(const uint8_t*state,NFVisibilityRead read,void*context,uint32_t*out){
 if(!state||!read||!out)return 0;
 uint8_t a[48],b[48],c[48],va[32*68],vb[32*68],vc[32*68];uint32_t result;
 if(!region_read(state,half(state+0xea),read,context,a,va))return 0;
 for(unsigned i=0;i<half(a+2);i++){
  unsigned first;if(!permitted_neighbor(state,va+i*68,read,context,&first))return 0;
  if(first==65535)continue;
  if(!region_read(state,first,read,context,b,vb))return 0;
  for(unsigned j=0;j<half(b+2);j++){
   unsigned second;if(!permitted_neighbor(state,vb+j*68,read,context,&second))return 0;
   if(second==65535)continue;
   if(!region_read(state,second,read,context,c,vc))return 0;
   unsigned n=half(c+2);
   if(!nfs_visibility_contains(vc,n*68,n,word(state+0xc0),word(state+0xc8),second,&result))return 0;
   if(result!=65535){unsigned link=half(c+0x20);if(!half(c+8)&&link!=65535){if(link>=512)return 0;result=link;}*out=result;return 1;}
  }
 }
 *out=65535;return 1;
}
__declspec(dllexport) int nfs_visibility_pair(uint8_t*state,unsigned selected,const uint32_t point[4],NFVisibilityRead read,void*context,uint32_t out[2]){
 if(!state||selected>=512||!point||!read||!out)return 0;
 uint8_t s[256];uint32_t result[2],x=sar(point[0],8),z=sar(point[1],8),v;
 memcpy(s,state,256);put(s+0xea,(uint16_t)selected);
 v=x+point[2];memcpy(s+0xc0,&v,4);v=z+point[3];memcpy(s+0xc8,&v,4);
 if(!nfs_visibility_select(s,read,context,result))return 0;
 if(result[0]==65535){if(!nfs_visibility_fallback(s,read,context,result))return 0;if(result[0]==65535)result[0]=selected;}
 v=x-point[2];memcpy(s+0xc0,&v,4);v=z-point[3];memcpy(s+0xc8,&v,4);
 if(!nfs_visibility_select(s,read,context,result+1))return 0;
 memcpy(state,s,256);memcpy(out,result,sizeof(result));return 1;
}
__declspec(dllexport) int nfs_visibility_query(uint8_t*state,uint32_t*selected,unsigned recovery,const uint32_t base[2],const uint32_t matrix[12],NFVisibilityRead read,void*context,uint32_t out[2]){
 if(!state||!selected||*selected>=512||recovery>=512||!base||!matrix||!read||!out)return 0;
 uint8_t s[256];uint32_t region=*selected,found,offset[3],pair[2],v;
 memcpy(s,state,256);put(s+0xea,(uint16_t)region);
 v=sar(base[0],8);memcpy(s+0xc0,&v,4);v=sar(base[1],8);memcpy(s+0xc8,&v,4);
 if(!nfs_visibility_select(s,read,context,&found))return 0;
 /* Original ignores a successful neighbor result at this preliminary step. */
 if(found==65535)region=recovery;
 if(!nfs_visibility_offset(matrix,offset))return 0;
 uint32_t point[4]={base[0],base[1],offset[0],offset[2]};
 if(!nfs_visibility_pair(s,region,point,read,context,pair))return 0;
 memcpy(state,s,256);*selected=region;memcpy(out,pair,sizeof(pair));return 1;
}
/* Root record initialization after descriptor selection: viewport comes from
   state +58..+5E, optional descriptor +22 redirects the selected root. Spatial
   selection/fallback of the selected descriptor remains the caller's job. */
__declspec(dllexport) int nfs_visibility_root(const uint8_t*state,unsigned selected,NFVisibilityRead read,void*context,uint8_t*out){
 if(!state||selected>=512||!read||!out)return 0;
 uint8_t descriptor[48],record[16]={0};
 if(!indexed_read(read,context,word(state+0x14),selected,48,descriptor,48))return 0;
 unsigned redirect=half(descriptor+0x22),root=redirect==65535?selected:redirect;
 if(root>=512)return 0;
 put(record,(uint16_t)root);memcpy(record+2,state+0x58,8);memcpy(out,record,16);return 1;
}
__declspec(dllexport) int nfs_visibility_choose_root(const uint8_t*state,const uint32_t pair[2],NFVisibilityRead read,void*context,uint32_t*selected,uint8_t root[16]){
 if(!state||!pair||!read||!selected||!root)return 0;
 if((pair[0]>=512&&pair[0]!=65535)||(pair[1]>=512&&pair[1]!=65535))return 0;
 uint32_t chosen=pair[0]==65535?pair[1]:pair[0];uint8_t seed[16];
 if(!nfs_visibility_root(state,chosen,read,context,seed))return 0;
 memcpy(root,seed,2);*selected=chosen;return 1;
}
/* Standalone 03004C74 builder using a coherent, immutable snapshot reader.
   Caller supplies the initialized first queue record. Remaining queue bytes
   are retained exactly as in the original. Failures publish no partial data. */
__declspec(dllexport) int nfs_visibility_build(uint8_t*state,uint8_t*queue,uint8_t*groups,NFVisibilityRead read,void*context,const uint32_t*reciprocal){
 if(!state||!queue||!groups||!read||!reciprocal){visibility_failure_stage=50;return /* diagnostic */ 0;}
 uint8_t s[256],q[NF_VISIBILITY_QUEUE_BYTES],g[4096]={0},projection[64],viewport[16],descriptor[48],vertices[32*68];uint32_t camera[12];
 memcpy(s,state,256);memcpy(q,queue,NF_VISIBILITY_QUEUE_BYTES);
 if(!read(context,word(s+0x50),projection,64)||!read(context,word(s+0x54),camera,48)||!read(context,word(projection+4),viewport,16)){visibility_failure_stage=51;return /* diagnostic */ 0;}
 uint32_t total=1,next=1,linked=0;
 for(unsigned i=0;i<total;i++){
  /* Original03004D38 stops expanding after a whole region pushes total
     beyond20. Storage capacity is separate: that final region can emit more. */
  if(total>20)break;
  uint8_t*parent=q+i*16;unsigned index=half(parent);
  if(index>=512||!indexed_read(read,context,word(s+0x14),index,48,descriptor,48)){visibility_failure_stage=53;return /* diagnostic */ 0;}
  if(half(parent+12)<=4){
   unsigned count=half(descriptor+2);if(count>32){visibility_failure_stage=54;return /* diagnostic */ 0;}
   if(!indexed_read(read,context,word(s+0x10),half(descriptor),68,vertices,count*68)){visibility_failure_stage=55;return /* diagnostic */ 0;}
   if(!nfs_visibility_traverse(s,descriptor,vertices,count*68,camera,projection,parent,reciprocal,q,g,&next,&total,i==0)){return /* traversal stage retained */ 0;}
  }
  if(!linked&&!nfs_visibility_append(q,NF_VISIBILITY_QUEUE_CAPACITY,&next,&total,&linked,parent,half(descriptor+0x20),half(viewport),half(viewport+8))){visibility_failure_stage=57;return /* diagnostic */ 0;}
 }
 if(total>NF_VISIBILITY_QUEUE_CAPACITY||!nfs_visibility_merge(q,total,g,512)){visibility_failure_stage=58;return /* diagnostic */ 0;}
 put(s+0xee,(uint16_t)total);
 memcpy(state,s,256);memcpy(queue,q,NF_VISIBILITY_QUEUE_BYTES);memcpy(groups,g,4096);return 1;
}
__declspec(dllexport) int nfs_visibility_build_pair(uint8_t*state,uint8_t*queue,uint8_t*groups,const uint32_t pair[2],uint32_t*selected,NFVisibilityRead read,void*context,const uint32_t*reciprocal){
 if(!state||!queue||!groups||!pair||!selected||!read||!reciprocal)return 0;
 uint8_t s[256],q[NF_VISIBILITY_QUEUE_BYTES],g[4096];uint32_t region;
 memcpy(s,state,256);memcpy(q,queue,NF_VISIBILITY_QUEUE_BYTES);memcpy(g,groups,4096);
 memset(q,0,16);memcpy(q+2,s+0x58,8);
 visibility_failure_stage=4;if(!nfs_visibility_choose_root(s,pair,read,context,&region,q))return 0;
 visibility_failure_stage=5;if(!nfs_visibility_build(s,q,g,read,context,reciprocal))return 0;
 memcpy(state,s,256);memcpy(queue,q,NF_VISIBILITY_QUEUE_BYTES);memcpy(groups,g,4096);*selected=region;return 1;
}
typedef struct {NFVisibilityRead read;void*context;uint32_t address;uint32_t matrix[12];} NFVisibilityView;
static int visibility_view_read(void*context,uint32_t address,void*out,size_t size){
 NFVisibilityView*v=context;uint64_t end=(uint64_t)address+size,view_end=(uint64_t)v->address+48;
 if(end>UINT32_MAX||!v->read(v->context,address,out,size))return 0;
 uint64_t lo=address>v->address?address:v->address,hi=end<view_end?end:view_end;
 if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),(const uint8_t*)v->matrix+(size_t)(lo-v->address),(size_t)(hi-lo));
 return 1;
}
__declspec(dllexport) int nfs_visibility_evaluate(uint8_t*state,uint8_t*queue,uint8_t*groups,uint32_t*selected,unsigned recovery,const uint32_t base[2],const uint32_t query_matrix[12],const uint32_t view_matrix[12],NFVisibilityRead read,void*context,const uint32_t*reciprocal){
 if(!state||!queue||!groups||!selected||!base||!query_matrix||!view_matrix||!read||!reciprocal)return 0;
 uint8_t s[256],q[NF_VISIBILITY_QUEUE_BYTES],g[4096];uint32_t region=*selected,pair[2];
 memcpy(s,state,256);memcpy(q,queue,NF_VISIBILITY_QUEUE_BYTES);memcpy(g,groups,4096);
 NFVisibilityView view={read,context,word(s+0x54),{0}};
 if(view.address>UINT32_MAX-48)return 0;
 memcpy(view.matrix,view_matrix,48);
 if(!nfs_visibility_query(s,&region,recovery,base,query_matrix,read,context,pair)||
    !nfs_visibility_build_pair(s,q,g,pair,&region,visibility_view_read,&view,reciprocal))return 0;
 memcpy(state,s,256);memcpy(queue,q,NF_VISIBILITY_QUEUE_BYTES);memcpy(groups,g,4096);*selected=region;return 1;
}








__declspec(dllexport) int nfs_visibility_static_child_record(const uint8_t*state,const uint8_t record[16],unsigned pass,NFVisibilityRead read,void*context,const uint32_t*reciprocal,uint8_t out[16]){
 if(!state||!record||pass>1||!read||!reciprocal||!out)return -1;
 if(pass)return 0; /*030028CC second pass bypasses static descriptor links. */
 uint8_t descriptor[48],s[256],viewport[16],edges[32*52]={0},stream[64*24]={0};uint32_t geometry[2];
 memcpy(s,state,256);
 int status=nfs_visibility_region_setup(s,record,read,context,viewport,descriptor,geometry);
 if(status!=1)return status;
 /*030028D4 sibling-chain mode enters before ordinary parent geometry. */
 if(descriptor[0x12]&8)return -1;
 unsigned child=half(descriptor+6);if(child==65535)return 0;if(child>=512)return -1;
 status=nfs_visibility_region_reconstruct(s,record,read,context,reciprocal,edges,sizeof(edges),stream,sizeof(stream));
 if(status!=1)return status;
 uint8_t result[16];memcpy(result,record,16);put(result,(uint16_t)child);memcpy(out,result,16);return 1;
}

__declspec(dllexport) int nfs_visibility_object_region_prepare(uint8_t state[256],const uint8_t object[164],const uint8_t parent[16],uint8_t record[16]){
 if(!state||!object||!parent||!record)return -1;
 uint8_t owned[256],result[16];memcpy(owned,state,256);memcpy(result,record,16);memcpy(owned+226,parent+2,4);
 int status=nfs_visibility_object_region(owned,object,result);if(status<0)return status;
 memcpy(state,owned,256);if(status)memcpy(record,result,16);return status;
}
__declspec(dllexport) int nfs_visibility_object_branch_prepare(uint8_t state[256],const uint8_t object[164],const uint8_t parent[16],const uint32_t matrix[12],uint32_t xyz[3],unsigned*branch,uint8_t record[16]){
 if(!state||!object||!parent||!matrix||!xyz||!branch||!record)return -1;
 uint8_t owned[256],result[16];uint32_t position[3];memcpy(owned,state,256);memcpy(result,record,16);
 if(!nfs_visibility_object_draw_setup(owned,parent,object,matrix,position))return -1;
 int selected=nfs_visibility_object_region(owned,object,result);if(selected<0)return -1;
 memcpy(state,owned,256);memcpy(xyz,position,12);*branch=(unsigned)selected;
 if(selected)memcpy(record,result,16);return 1;
}

__declspec(dllexport) int nfs_visibility_object_sources(const uint8_t state[256],const uint8_t record[16],NFVisibilityRead read,void*context,NFVisibilityObjectSource*out,unsigned capacity,unsigned*out_count){
 if(!state||!record||!read||!out||!out_count)return 0;
 unsigned region=half(record);uint8_t descriptor[48];uint32_t regions[512],count=1,replaces=0;
 if(region>=512||!indexed_read(read,context,word(state+20),region,48,descriptor,48))return 0;
 regions[0]=region;
 if(descriptor[18]&8){if(!nfs_visibility_region_links(state,descriptor,read,context,regions,512,&count,&replaces)||!replaces)return 0;}
 NFVisibilityObjectSource result[512];unsigned n=0;
 for(unsigned i=0;i<count;i++){
  uint16_t head;if(!indexed_read(read,context,word(state+12),regions[i],2,&head,2))return 0;
  if(head==65535)continue;
  if(head>=512||n>=capacity)return 0;
  result[n++]=(NFVisibilityObjectSource){regions[i],head};
 }
 memcpy(out,result,n*sizeof(*out));*out_count=n;return 1;
}

__declspec(dllexport) int nfs_visibility_object_dispatch_begin(NFVisibilityObjectDispatch*out,const NFVisibilityObjectSource*sources,unsigned count,unsigned object_count){
 if(!out||count>512||object_count>512||(count&&!sources))return 0;
 for(unsigned i=0;i<count;i++)if(sources[i].region>=512||sources[i].head>=object_count)return 0;
 NFVisibilityObjectDispatch owned={0};owned.count=count;owned.object_count=object_count;
 if(count)memcpy(owned.sources,sources,count*sizeof(*sources));
 if(nfs_visibility_object_cursor_begin(&owned.collector.cursor,65535,object_count)<0)return 0;
 *out=owned;return 1;
}
__declspec(dllexport) int nfs_visibility_object_dispatch_next(NFVisibilityObjectDispatch*d,unsigned*region){
 if(!d||!region||d->count>512||d->next>d->count||d->object_count>512||d->collector.awaiting_callback||d->collector.cursor.current!=65535)return -1;
 if(d->next==d->count)return 0;
 NFVisibilityObjectSource source=d->sources[d->next];NFVisibilityObjectCursor cursor;
 if(source.region>=512||nfs_visibility_object_cursor_begin(&cursor,source.head,d->object_count)!=1)return -1;
 d->collector.cursor=cursor;d->next++;*region=source.region;return 1;
}

__declspec(dllexport) int nfs_visibility_region_object_gate(const uint8_t state[256],const uint8_t record[16],unsigned pass,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768]){
 if(!state||!record||pass>1||!read||!reciprocal)return -1;
 uint8_t owned[256],descriptor[48],viewport[16];uint32_t geometry[2];memcpy(owned,state,256);
 int status=nfs_visibility_region_setup(owned,record,read,context,viewport,descriptor,geometry);if(status!=1)return status;
 if(!word(owned+120))return 0;
 if(pass)return 1;
 if((descriptor[18]&8)||!(half(record+10)&128))return 0;
 uint8_t edges[32*52]={0},stream[64*24]={0};
 return nfs_visibility_region_reconstruct(owned,record,read,context,reciprocal,edges,sizeof(edges),stream,sizeof(stream));
}

__declspec(dllexport) int nfs_visibility_region_object_plan(const uint8_t state[256],const uint8_t record[16],unsigned pass,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],NFVisibilityObjectSource*out,unsigned capacity,unsigned*out_count,unsigned*eligible){
 if(!out||!out_count||!eligible)return -1;
 int gate=nfs_visibility_region_object_gate(state,record,pass,read,context,reciprocal);if(gate<0)return -1;
 NFVisibilityObjectSource staged[512];unsigned count=0;
 if(gate&&!nfs_visibility_object_sources(state,record,read,context,staged,512,&count))return -1;
 if(count>capacity)return -1;
 memcpy(out,staged,count*sizeof(*out));*out_count=count;*eligible=(unsigned)gate;return 1;
}
__declspec(dllexport) int nfs_visibility_region_actions(const uint8_t state[256],const uint8_t record[16],unsigned pass,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],NFVisibilityRegionAction*out,unsigned capacity,unsigned*out_count){
 if(!state||!record||pass>1||!read||!reciprocal||!out||!out_count)return 0;
 uint8_t owned[256],descriptor[48],viewport[16];uint32_t geometry[2];NFVisibilityRegionAction actions[515];unsigned n=0;
 memcpy(owned,state,256);int status=nfs_visibility_region_setup(owned,record,read,context,viewport,descriptor,geometry);
 if(status<0)return 0;
 if(status==1){
  if(pass){if(word(owned+120)){actions[n]=(NFVisibilityRegionAction){3,pass,0,{0}};memcpy(actions[n++].record,record,16);}}
  else if(descriptor[18]&8){
   uint32_t links[512];unsigned count,replaces;
   if(!nfs_visibility_region_links(owned,descriptor,read,context,links,512,&count,&replaces)||!replaces)return 0;
   for(unsigned i=0;i<count;i++){actions[n]=(NFVisibilityRegionAction){2,0,0,{0}};memcpy(actions[n].record,record,16);put(actions[n++].record,(uint16_t)links[i]);}
  }else{
   uint8_t edges[32*52]={0},stream[64*24]={0},vertices[32*68];NFVisibilityWallDraw walls[32];unsigned wall_count;uint32_t deferred;
   status=nfs_visibility_region_reconstruct(owned,record,read,context,reciprocal,edges,sizeof(edges),stream,sizeof(stream));if(status<0)return 0;
   if(status==1){
    if(!read(context,geometry[0],vertices,geometry[1]*68u)||!nfs_visibility_wall_draw_plan(owned,vertices,geometry[1],edges,0,read,context,walls,32,&wall_count,&deferred))return 0;
    actions[n]=(NFVisibilityRegionAction){1,0,0,{0}};memcpy(actions[n++].record,record,16);
    unsigned child=half(descriptor+6);if(child!=65535){if(child>=512)return 0;actions[n]=(NFVisibilityRegionAction){2,0,0,{0}};memcpy(actions[n].record,record,16);put(actions[n++].record,(uint16_t)child);}
    if((half(record+10)&128)&&word(owned+120)){actions[n]=(NFVisibilityRegionAction){3,0,0,{0}};memcpy(actions[n++].record,record,16);}
    deferred&=255;if(deferred){actions[n]=(NFVisibilityRegionAction){4,0,deferred,{0}};memcpy(actions[n++].record,record,16);}
   }
  }
 }
 if(n>capacity)return 0;
 memcpy(out,actions,n*sizeof(*out));*out_count=n;return 1;
}
