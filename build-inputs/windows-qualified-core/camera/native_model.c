#include <stdlib.h>
#include <stdint.h>
#include <string.h>
int nfs_model_clip_ring(const int32_t*,unsigned,const int32_t[4],unsigned,const uint32_t*,int32_t*,unsigned,unsigned*);
static uint32_t get32(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static int32_t get16(const uint8_t*p){return (int16_t)(p[0]|(unsigned)p[1]<<8);}
static int32_t asr(uint32_t v,unsigned n){return (int32_t)((v>>n)|((v&0x80000000u)?(~0u<<(32-n)):0));}
static void set16(uint8_t*p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
/* Original ARM 030045E0 model transform/projection contract.
   Source = signed XYZ int16 triples; destination = signed XY int16 pairs.
   Matrix = column-major 3x3 Q14 plus three integer translations.
   Original rejects the entire model on unsigned depth > 0x6000, preserving
   earlier writes. Negative depth therefore also rejects. Caller supplies
   the original reciprocal table through index 0x6000 inclusive.
   This is the exact integer reference, not temporal interpolation. */
__declspec(dllexport) int nfs_model_project(const uint8_t*matrix,const uint8_t*source,unsigned count,
 uint32_t scale,int32_t center_x,int32_t center_y,const uint32_t*reciprocal,uint8_t*dest){
 for(unsigned i=0;i<count;i++){
  uint32_t x=(uint32_t)get16(source+i*6),y=(uint32_t)get16(source+i*6+2),z=(uint32_t)get16(source+i*6+4);
  uint32_t cx=get32(matrix+36)+(uint32_t)asr(x*get32(matrix)+y*get32(matrix+12)+z*get32(matrix+24),14);
  uint32_t cy=get32(matrix+40)+(uint32_t)asr(x*get32(matrix+4)+y*get32(matrix+16)+z*get32(matrix+28),14);
  uint32_t cz=get32(matrix+44)+(uint32_t)asr(x*get32(matrix+8)+y*get32(matrix+20)+z*get32(matrix+32),14);
  if(cz>0x6000)return 0;
  uint32_t factor=(uint32_t)asr(scale*reciprocal[cz],8);
  set16(dest+i*4,(uint32_t)center_x+(uint32_t)asr(cx*factor,16));
  set16(dest+i*4+2,(uint32_t)center_y+(uint32_t)asr(cy*factor,16));
 }
 return 1;
}

/* 03004804..0300486C: first-three-vertex signed determinant with ARM
   32-bit wrap. Collinear faces proceed to the polygon rasterizer. */
__declspec(dllexport) int nfs_model_face_visible(const uint8_t*points,unsigned point_count,const uint16_t*indices,unsigned face_count,int*out){
 if(!points||!indices||!out||face_count<3)return 0;
 unsigned a=indices[0],b=indices[1],c=indices[2];
 if(a>=point_count||b>=point_count||c>=point_count)return 0;
 int32_t ax=get16(points+a*4),ay=get16(points+a*4+2);
 int32_t bx=get16(points+b*4),by=get16(points+b*4+2);
 int32_t cx=get16(points+c*4),cy=get16(points+c*4+2);
 uint32_t determinant=(uint32_t)(by-ay)*(uint32_t)(cx-ax)-(uint32_t)(cy-ay)*(uint32_t)(bx-ax);
 *out=(determinant&0x80000000u)==0;return 1;
}

/* Original 03005824 rectangle classifier: right/bottom exclusive, requires
   at least one vertex inside each axis even if a ring crosses the rectangle. */
__declspec(dllexport) int nfs_model_polygon_classify(const uint8_t*points,unsigned point_count,const uint16_t*indices,unsigned count,const int32_t*rect,int*out){
 if(!points||!indices||!rect||!out||!count||count>32)return 0;
 unsigned flags=0,inside_x=0,inside_y=0;
 for(unsigned i=0;i<count;i++){
  if(indices[i]>=point_count)return 0;
  int32_t x=get16(points+indices[i]*4),y=get16(points+indices[i]*4+2);
  if(x<rect[0]||x>=rect[2])flags|=1;else inside_x++;
  if(y<rect[1]||y>=rect[3])flags|=2;else inside_y++;
 }
 *out=inside_x&&inside_y?(int)flags:4;return 1;
}

/* Original 03005920 Q8 texture stepping, including independent fractional
   carry for U and V. Index zero is opaque in this model writer. */
__declspec(dllexport) int nfs_model_span_addresses(uint32_t texture,uint32_t destination,unsigned count,unsigned shift,uint32_t u,uint32_t v,uint32_t du,uint32_t dv,uint32_t*source_out,uint32_t*destination_out){
 if(count>240||shift>10||(count&&(!source_out||!destination_out)))return 0;
 uint32_t address=texture+(uint32_t)asr(u,8)+((uint32_t)asr(v,8)<<shift);
 uint32_t fu=u<<24,fv=v<<24,su=du<<24,sv=dv<<24;
 uint32_t increment=(uint32_t)asr(du,8)+((uint32_t)asr(dv,8)<<shift);
 for(unsigned i=0;i<count;i++){
  source_out[i]=address;destination_out[i]=destination+i;
  uint32_t nu=fu+su,nv=fv+sv;
  address+=increment+(nu<fu)+((nv<fv)?(1u<<shift):0);fu=nu;fv=nv;
 }
 return 1;
}

/* 03003EC8..03003F34: inclusive horizontal row span. Multiplication wraps
   before signed shift; this differs from a full-width fixed-point multiply. */
__declspec(dllexport) int nfs_model_row_plan(uint32_t left,uint32_t right,uint32_t left_u,uint32_t left_v,uint32_t right_u,uint32_t right_v,uint32_t row_base,const uint32_t*table,uint32_t out[6]){
 if(!table||!out)return 0;
 if((int32_t)right<=(int32_t)left){memset(out,0,24);return 1;}
 int32_t x=asr(left,16),width=asr(right,16)-x+1;
 if(width<=0||width>=32768)return 0;
 uint32_t factor=(uint32_t)asr(table[width],8);
 uint32_t values[6]={row_base+(uint32_t)x,(uint32_t)width,left_u,left_v,(uint32_t)asr(factor*(right_u-left_u),16),(uint32_t)asr(factor*(right_v-left_v),16)};
 memcpy(out,values,sizeof(values));return 1;
}

/* Original 03003A20..03003B14 ascending edge arithmetic. UV inputs are
   unsigned source halfwords. X uses fixed16; U/V use Q8 after asset scaling. */
__declspec(dllexport) int nfs_model_edge_plan(const int16_t*start,const int16_t*end,const uint16_t*uv_start,const uint16_t*uv_end,unsigned shift,unsigned height,const uint32_t*table,uint32_t out[7]){
 if(!start||!end||!uv_start||!uv_end||!table||!out||shift>10||height>1024)return 0;
 int dy=(int)end[1]-start[1];if(dy<=0||dy>=32768)return 0;
 uint32_t factor=(uint32_t)asr(table[dy],8);
 uint32_t u0=(uint32_t)asr((uint32_t)uv_start[0]<<shift,7),u1=(uint32_t)asr((uint32_t)uv_end[0]<<shift,7);
 uint32_t v0=((uint32_t)uv_start[1]*height)>>7,v1=((uint32_t)uv_end[1]*height)>>7;
 uint32_t values[7]={(uint32_t)dy,(uint32_t)(int32_t)start[0]<<16,u0,v0,factor*(uint32_t)((int)end[0]-start[0]),(uint32_t)asr(factor*(u1-u0),16),(uint32_t)asr(factor*(v1-v0),16)};
 memcpy(out,values,sizeof(values));return 1;
}

/* Owned uncut source ring -> exact row writer arguments; atomic publication.
   Clipped rings must first pass the separately verified polygon clip path. */
__declspec(dllexport) int nfs_model_ring_rows(const int16_t*points,const uint16_t*uv,unsigned n,unsigned shift,unsigned height,uint32_t base,const uint32_t*table,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(!points||!uv||!table||!out||!out_count||n<3||n>64||capacity>1000)return 0;
 unsigned top=0;for(unsigned i=1;i<n;i++)if(points[i*2+1]<points[top*2+1])top=i;
 int y=points[top*2+1],remaining[2]={(int)n,(int)n},life[2]={0,0};unsigned index[2]={top,top},count=0;
 uint32_t values[2][6]={{0}},rows[6000];
 for(unsigned iteration=0;iteration<1000;iteration++){
  for(unsigned side=0;side<2;side++){
   if(--life[side]>0)continue;
   for(;;){
    unsigned start=index[side],end=side?(start+n-1)%n:(start+1)%n;
    if(--remaining[side]<0||points[end*2+1]<points[start*2+1]){memcpy(out,rows,count*6*sizeof(*out));*out_count=count;return 1;}
    index[side]=end;if(points[end*2+1]==points[start*2+1])continue;
    uint32_t edge[7];if(!nfs_model_edge_plan(points+start*2,points+end*2,uv+start*2,uv+end*2,shift,height,table,edge))return 0;
    life[side]=(int)edge[0];memcpy(values[side],edge+1,sizeof(values[side]));break;
   }
  }
  uint32_t row[6];if(!nfs_model_row_plan(values[0][0],values[1][0],values[0][1],values[0][2],values[1][1],values[1][2],base+(uint32_t)y*240,table,row))return 0;
  if(row[1]){if(count>=capacity)return 0;memcpy(rows+count*6,row,sizeof(row));count++;}
  for(unsigned side=0;side<2;side++)for(unsigned k=0;k<3;k++)values[side][k]+=values[side][k+3];
  y++;
 }
 return 0;
}

/* One owned source face: native visibility, indexed XY/UV gather and row walk.
   Rejected/back-facing faces succeed with zero rows; unsupported clipping fails.
   Output and count remain unchanged on any failure. */
__declspec(dllexport) int nfs_model_face_rows(const uint8_t*points,unsigned point_count,const uint8_t*uv,unsigned uv_count,const uint16_t*vertices,const uint16_t*uv_indices,unsigned n,const int32_t*rect,unsigned shift,unsigned height,uint32_t base,const uint32_t*table,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(!points||!uv||!vertices||!uv_indices||!rect||!table||!out||!out_count||n<3||n>32)return 0;
 for(unsigned i=0;i<n;i++)if(vertices[i]>=point_count||uv_indices[i]>=uv_count)return 0;
 int visible;if(!nfs_model_face_visible(points,point_count,vertices,n,&visible))return 0;
 if(!visible){*out_count=0;return 1;}
 int classification;if(!nfs_model_polygon_classify(points,point_count,vertices,n,rect,&classification))return 0;
 if(classification==4){*out_count=0;return 1;}

 int16_t ring[128];uint16_t tex[128];
 for(unsigned i=0;i<n;i++){
  const uint8_t*p=points+vertices[i]*4,*t=uv+uv_indices[i]*4;
  int x=get16(p),y=get16(p+2);
  ring[i*2]=(int16_t)x;ring[i*2+1]=(int16_t)y;tex[i*2]=(uint16_t)get16(t);tex[i*2+1]=(uint16_t)get16(t+2);
 }
 if(classification){int32_t input[128],clipped[256];unsigned count;for(unsigned i=0;i<n;i++){input[i*4]=ring[i*2];input[i*4+1]=ring[i*2+1];input[i*4+2]=tex[i*2];input[i*4+3]=tex[i*2+1];}
  if(!nfs_model_clip_ring(input,n,rect,(unsigned)classification,table,clipped,64,&count))return 0;
  if(count<3){*out_count=0;return 1;}n=count;for(unsigned i=0;i<n;i++){ring[i*2]=(int16_t)clipped[i*4];ring[i*2+1]=(int16_t)clipped[i*4+1];tex[i*2]=(uint16_t)clipped[i*4+2];tex[i*2+1]=(uint16_t)clipped[i*4+3];}}
 return nfs_model_ring_rows(ring,tex,n,shift,height,base,table,out,capacity,out_count);
}

/* Whole owned model. config: vertex count, scale, signed centers, texture shift,
   height, destination base, face count. Faces are65 halfwords: count,32 vertex
   indices,32 UV indices. Output records are selected-face ordinal + six words. */
__declspec(dllexport) int nfs_model_mesh_rows(const uint8_t*matrix,const uint8_t*local,const uint8_t*uv,unsigned uv_count,const uint16_t*faces,const uint32_t*config,const int32_t*rect,const uint32_t*table,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(!matrix||!local||!uv||!faces||!config||!rect||!table||!out||!out_count||!config[0]||config[0]>4096||config[7]>4096||capacity>65536)return 0;
 uint8_t*points=malloc(config[0]*4);uint32_t*rows=malloc((capacity?capacity:1)*7*sizeof(*rows));int ok=0;unsigned total=0,selected=0;
 if(!points||!rows)goto done;
 if(!nfs_model_project(matrix,local,config[0],config[1],(int32_t)config[2],(int32_t)config[3],table,points))goto done;
 for(unsigned fi=0;fi<config[7];fi++){
  const uint16_t*face=faces+fi*65;unsigned n=face[0];if(n<3||n>32)goto done;
  for(unsigned k=0;k<n;k++)if(face[1+k]>=config[0]||face[33+k]>=uv_count)goto done;
  int visible;if(!nfs_model_face_visible(points,config[0],face+1,n,&visible))goto done;
  if(!visible)continue;
  uint32_t span[6000];unsigned count=0;
  if(!nfs_model_face_rows(points,config[0],uv,uv_count,face+1,face+33,n,rect,config[4],config[5],config[6],table,span,1000,&count)||count>capacity-total)goto done;
  for(unsigned k=0;k<count;k++){rows[total*7]=selected;memcpy(rows+total*7+1,span+k*6,24);total++;}
  selected++;
 }
 memcpy(out,rows,total*7*sizeof(*out));*out_count=total;ok=1;
 done:free(points);free(rows);return ok;
}

/* Raw owned blocks: context,descriptor,transform,framebuffer,vertices,
   face counts,vertex indices,UV indices,UV pairs,rectangle. No bus reads. */
__declspec(dllexport) int nfs_model_source_rows(const uint8_t*const blocks[10],const unsigned sizes[10],const uint32_t*table,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(!blocks||!sizes||!table||!out||!out_count)return 0;
 for(unsigned i=0;i<10;i++)if(!blocks[i])return 0;
 if(sizes[0]<68||sizes[1]<40||sizes[2]<48||sizes[3]<16||sizes[9]!=16||sizes[8]%4)return 0;
 const uint8_t*context=blocks[0],*descriptor=blocks[1];unsigned n=(unsigned)(uint16_t)get16(descriptor+36),nf=(unsigned)(uint16_t)get16(descriptor+34);
 if(!n||n>2048||!nf||nf>512||sizes[4]!=n*6||sizes[5]!=nf)return 0;
 unsigned corners=0;for(unsigned i=0;i<nf;i++){unsigned count=blocks[5][i];if(count<3||count>32)return 0;corners+=count;}
 if(corners>4096||sizes[6]!=corners*2||sizes[7]!=corners*2)return 0;
 uint16_t*faces=calloc(nf*65,sizeof(*faces));if(!faces)return 0;
 unsigned offset=0;for(unsigned i=0;i<nf;i++){
  unsigned count=blocks[5][i];faces[i*65]=(uint16_t)count;
  for(unsigned j=0;j<count;j++){faces[i*65+1+j]=(uint16_t)get16(blocks[6]+(offset+j)*2);faces[i*65+33+j]=(uint16_t)get16(blocks[7]+(offset+j)*2);}offset+=count;
 }
 uint32_t config[8]={n,get32(context+64),(uint32_t)get16(blocks[3]+8),(uint32_t)get16(blocks[3]+10),(uint16_t)get16(context+56),(uint16_t)get16(context+58),get32(blocks[3]),nf};
 int32_t rect[4];memcpy(rect,blocks[9],16);
 int ok=nfs_model_mesh_rows(blocks[2],blocks[4],blocks[8],sizes[8]/4,faces,config,rect,table,out,capacity,out_count);free(faces);return ok;
}

/* Atomic native model command execution against caller-owned VRAM.
   Texture bytes are owned at draw entry; index zero is opaque. */
__declspec(dllexport) int nfs_model_rows_write(const uint32_t*rows,unsigned count,unsigned shift,uint32_t texture_address,const uint8_t*texture,size_t texture_size,uint8_t*vram,size_t vram_size){
 if(!rows||!texture||!vram||count>65536||vram_size!=0x18000)return 0;
 uint8_t*next=malloc(vram_size);if(!next)return 0;memcpy(next,vram,vram_size);int ok=0;
 for(unsigned row=0;row<count;row++){
  const uint32_t*r=rows+row*7+1;uint32_t source[240],destination[240];
  if(!nfs_model_span_addresses(texture_address,r[0],r[1],shift,r[2],r[3],r[4],r[5],source,destination))goto done;
  for(unsigned i=0;i<r[1];i++){
   if(source[i]<texture_address||(uint64_t)source[i]-texture_address>=texture_size||destination[i]<0x06000000||(uint64_t)destination[i]-0x06000000>=vram_size)goto done;
   next[destination[i]-0x06000000]=texture[source[i]-texture_address];
  }
 }
 memcpy(vram,next,vram_size);ok=1;
 done:free(next);return ok;
}


/* Original03003FCC edge clipping. XY signed, UV unsigned values in eight words.
   Return flags1kept/2startclipped/4endclipped; output unchanged on rejection. */
__declspec(dllexport) int nfs_model_clip_edge(int32_t low,int32_t high,unsigned axis,unsigned has_uv,const int32_t input[8],const uint32_t*table,int32_t output[8],unsigned*flags){
 if(!input||!table||!output||!flags||axis>1||low>high)return 0;
 int32_t p[8];memcpy(p,input,32);unsigned result=1,other=1-axis;
 if((p[axis]<low&&p[4+axis]<low)||(p[axis]>high&&p[4+axis]>high)){*flags=0;return 1;}
 for(unsigned end=0;end<2;end++){
  unsigned a=end*4,b=(1-end)*4;int32_t v=p[a+axis],boundary;
  if(v<low)boundary=low;else if(v>high)boundary=high;else continue;
  uint32_t distance=(uint32_t)(v<low?boundary-v:v-boundary);
  uint32_t denominator=(uint32_t)(v<low?p[b+axis]-v:v-p[b+axis]);
  if(!denominator||denominator>=32768)return 0;
  uint32_t factor=(uint32_t)asr(table[denominator],8)*distance;
  p[a+other]+=(int32_t)asr(factor*((uint32_t)p[b+other]-(uint32_t)p[a+other]),16);
  if(has_uv)for(unsigned k=2;k<4;k++)p[a+k]+=(int32_t)asr(factor*((uint32_t)p[b+k]-(uint32_t)p[a+k]),16);
  p[a+axis]=boundary;result|=end?4:2;
 }
 memcpy(output,p,32);*flags=result;return 1;
}

/* Original03004270 ring emission: horizontal then vertical, start vertex plus
   clipped end when present; narrow XY/UV after each original scratch pass. */
__declspec(dllexport) int nfs_model_clip_ring(const int32_t*input,unsigned n,const int32_t rect[4],unsigned classification,const uint32_t*table,int32_t*out,unsigned capacity,unsigned*out_count){
 if(!input||!rect||!table||!out||!out_count||n<3||n>32||capacity>64||classification>3)return 0;
 int32_t ring[256],next[256];memcpy(ring,input,n*16);
 for(unsigned axis=0;axis<2;axis++){
  if(!(classification&(1u<<axis)))continue;
  unsigned used=0;
  for(unsigned i=0;i<n;i++){
   int32_t edge[8],clipped[8];memcpy(edge,ring+i*4,16);memcpy(edge+4,ring+((i+1)%n)*4,16);unsigned flags;
   if(!nfs_model_clip_edge(rect[axis],rect[axis+2],axis,1,edge,table,clipped,&flags))return 0;
   if(!flags)continue;
   unsigned emitted=(flags&4)?2:1;if(used+emitted>64)return 0;
   for(unsigned j=0;j<emitted;j++){for(unsigned k=0;k<4;k++)next[(used+j)*4+k]=k<2?(int16_t)clipped[j*4+k]:(uint16_t)clipped[j*4+k];}
   used+=emitted;
  }
  n=used;memcpy(ring,next,n*16);if(!n)break;
 }
 if(n>capacity)return 0;memcpy(out,ring,n*16);*out_count=n;return 1;
}

