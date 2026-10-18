#include "preview_scissor.h"
#include "road_near_clip.h"
#include "road_triangulate.h"
#ifdef NF_ROAD_ATTRIBUTE_CORRECTION
#include "road_corrected_clip.h"
#include "road_near_continuity.h"
#include "road_clip_trace.h"
#ifdef NF_DIAGNOSTIC_ROAD_UV_POLICY
#include "road_uv_diagnostic.h"
#endif
#include "road_metadata_preview.h"
static NFRoadCameraMetadata preview_road_cameras[128];
static unsigned preview_road_cameras_present[128];
extern int nf_road_source_ring(const double*,unsigned,const NFRoadSourceAttributes*,const int32_t*,const int32_t*,const uint32_t*,double*,unsigned,unsigned*);
static uint64_t preview_source_road_rings;
static NFRoadSourceAttributes preview_road_attributes[128];
static unsigned preview_road_attributes_present[128];
static uint32_t preview_road_reciprocal[32768];
static int preview_road_reciprocal_ready;
static uint64_t preview_road_corrected_rings,preview_road_near_crossings;
static uint64_t preview_road_continuous_adjustments;
static int road_continuity_requested(void){
#ifdef NF_DIAGNOSTIC_ROAD_UV_POLICY
 /* Probe mode selection alone controls policy; avoid inherited double blending. */
 return 0;
#else
 const char*value=getenv("NF_CONTINUOUS_ROAD_UV");return value&&value[0]=='1'&&!value[1];
#endif
}
static int preview_road_table_load_path(const char*path){
 if(preview_road_reciprocal_ready)return 1;
 if(!path)return 0;
 FILE*f=fopen(path,"rb");if(!f)return 0;uint32_t table[32768];int ok=fread(table,4,32768,f)==32768&&fgetc(f)==EOF;fclose(f);
 if(!ok)return 0;for(unsigned i=0;i<32767;i++)if(table[i]!=16777216u/(i+1))return 0;
 memcpy(preview_road_reciprocal,table,sizeof(table));preview_road_reciprocal_ready=1;return 1;
}
static int preview_road_table_load(void){return preview_road_table_load_path(getenv("NF_ROAD_RECIPROCAL"));}
#endif
#ifdef NF_DIAGNOSTIC_ROAD_BOUNDS
#include "road_view_clip.h"
#endif
typedef struct {unsigned count;NFPoint3 vertices[32];double uv[64];GLuint texture;unsigned lit,intensity[2],width,height;GLuint variants[16];} RoadPreview;
static RoadPreview roads[128];static unsigned road_count;
static int load_roads(const char*path){
 PreviewInput*f=preview_input(2,path);uint32_t h[2];if(!f||!read_bytes(f,h,8)||h[0]!=0x31444652||h[1]>128)return 0;
 road_count=h[1];for(unsigned i=0;i<road_count;i++){
  uint32_t v[3];if(!read_bytes(f,v,12)||v[0]<3||v[0]>32||!v[1]||v[1]>1024||!v[2]||v[2]>1024)return 0;
  RoadPreview*r=roads+i;r->count=v[0];r->lit=0;r->width=v[1];r->height=v[2];unsigned bytes=v[1]*v[2]*4;uint8_t*p=malloc(bytes);if(!p)return 0;
  if(!read_bytes(f,r->vertices,v[0]*sizeof(NFPoint3))||!read_bytes(f,r->uv,v[0]*2*sizeof(double))||!read_bytes(f,p,bytes)){free(p);return 0;}
  if(preview_world_indices[i]&&!model_zero_shader()){free(p);return 0;}
  r->texture=preview_wall_states[i]?wall_indexed_texture(v[1],v[2],p,preview_wall_states[i],preview_wall_indices[i]):model_zero_texture(v[1],v[2],p,preview_world_indices[i]);free(p);if(!r->texture)return 0;
}preview_close(f);return 1;
}
#include "wall_lighting.h"
static void road_vertex_mode(const RoadVertex*v,unsigned affine){double depth_q=1/v->p.z,q=affine?1:depth_q;glTexCoord4d(v->u*q,v->v*q,0,q);
#ifdef NF_DIAGNOSTIC_DEPTH
 glVertex3d(v->p.x,v->p.y,-depth_q);
#else
 glVertex2d(v->p.x,v->p.y);
#endif
}
static int draw_road_range(NFRigidPose*poses,double alpha,const double*projection,unsigned first,unsigned end){
 if(first>end||end>road_count)return 0;
 NFRigidPose fixed={{0,0,0},{0,0,0,1}};
 for(unsigned ring=first;ring<end;ring++){
#ifdef NF_DIAGNOSTIC_SKIP_SURFACE
  if((int)ring==NF_DIAGNOSTIC_SKIP_SURFACE)continue;
#endif
  RoadPreview*r=roads+ring;NFPoint3 camera[32];RoadVertex in[32],out[64];unsigned n=0;
  #ifdef NF_ROAD_ATTRIBUTE_CORRECTION
  const char*source_mode=getenv("NF_SOURCE_ROAD_ENDPOINT");
  if(source_mode&&source_mode[0]=='1'&&!source_mode[1]&&preview_road_cameras_present[ring]){
   if(alpha!=0||!preview_road_attributes_present[ring]||!preview_road_reciprocal_ready||r->lit)return 0;
   int32_t params[3];for(unsigned k=0;k<3;k++){if(projection[k]!=(int32_t)projection[k])return 0;params[k]=(int32_t)projection[k];}
   double projected[64][5];NFRoadSourceAttributes*raw=preview_road_attributes+ring;
   if(!nf_road_source_ring((const double*)r->vertices,r->count,raw,preview_road_cameras[ring].matrix,params,preview_road_reciprocal,&projected[0][0],64,&n))return 0;
   for(unsigned i=0;i<n;i++){
    double q=projected[i][2];if(q<=0)return 0;
    out[i]=(RoadVertex){{projected[i][0],projected[i][1],16777216.0/q},projected[i][3]/((raw->affine?65536:q)*(1u<<raw->shift)*.5)+raw->offsets[0]/(256.0*(1u<<raw->shift)),projected[i][4]/((raw->affine?65536:q)*raw->stored_height*.5)+raw->offsets[1]/(256.0*raw->stored_height)};
   }
   preview_source_road_rings++;goto source_road_projected;
  }
  #endif
  if(!nf_rigid_scene_sample(poses,poses+1,&fixed,&fixed,alpha,r->vertices,r->count,camera))return 0;
  for(unsigned i=0;i<r->count;i++)in[i]=(RoadVertex){camera[i],r->uv[i*2],r->uv[i*2+1]};
  #ifdef NF_ROAD_ATTRIBUTE_CORRECTION
  if(preview_road_attributes_present[ring]){
   if(!preview_road_reciprocal_ready)return 0;
   if(road_continuity_requested()){unsigned adjusted;if(!texture_near_clip_continuous(in,r->count,out,preview_road_attributes+ring,preview_road_reciprocal,&n,&adjusted))return 0;preview_road_continuous_adjustments+=adjusted;}
   else if(!texture_near_clip_corrected(in,r->count,out,64,preview_road_attributes+ring,preview_road_reciprocal,&n))return 0;
#ifdef NF_DIAGNOSTIC_ROAD_UV_POLICY
   if(!road_uv_diagnostic(in,r->count,out,&n,preview_road_attributes+ring,preview_road_reciprocal,NF_DIAGNOSTIC_ROAD_UV_POLICY))return 0;
#endif
   preview_road_corrected_rings++;
   road_clip_trace(ring,r->vertices,in,out,preview_road_attributes+ring);
   for(unsigned i=0;i<r->count;i++)if((camera[i].z<64)!=(camera[(i+r->count-1)%r->count].z<64))preview_road_near_crossings++;
  }else
#endif
  n=texture_near_clip(in,r->count,out,64);
  if(n<3)continue;
  for(unsigned i=0;i<n;i++){out[i].p.x=projection[0]+projection[2]*out[i].p.x/out[i].p.z;out[i].p.y=projection[1]+projection[2]*out[i].p.y/out[i].p.z;}
  source_road_projected:;
  if(n<3)continue;
  RoadVertex triangles[192];unsigned triangle_count=road_triangulate(out,n,triangles);
#ifdef NF_DIAGNOSTIC_SURFACE_CLIP
  NF_DIAGNOSTIC_SURFACE_CLIP((int)ring);
#endif
  int shades[3240];int lit=r->lit?wall_shades(r,camera,projection,shades):0;
  if(preview_wall_states[ring]&&r->lit&&!lit){
#ifdef NF_DIAGNOSTIC_SURFACE_CLIP
   NF_DIAGNOSTIC_SURFACE_CLIP(-1);
#endif
   return 0;
  }
  unsigned columns=lit==2?3240:120,scale=lit==2?1:27;
  PreviewScissor surface_scissor=preview_scissor_save();
  for(unsigned column=0;column<(lit?columns:1u);){
   unsigned end_column=column+1;if(lit)while(end_column<columns&&shades[end_column]==shades[column])end_column++;
   GLuint selected=lit?r->variants[shades[column]]:r->texture;
   /* Indexed opaque-span metadata is currently supported only for unlit roads. */
   const uint8_t*wall_states=preview_wall_states[ring];
   if(wall_states&&lit)wall_states+=(size_t)(shades[column]+1)*r->width*r->height;
   int begun=0;
#ifdef NF_DIAGNOSTIC_WORLD_BEGIN_FAILURE
   if(!preview_world_indices[ring])begun=model_zero_begin(selected,NULL);
#else
   if(wall_states){begun=wall_zero_begin(selected,wall_states);if(begun&&preview_wall_indices[ring]&&preview_display_palette_valid)model_zero_uniform(model_zero_indexed_location,1);}
   else if(!(preview_world_indices[ring]&&lit))begun=model_zero_begin(selected,preview_world_indices[ring]);
#endif
   if(!begun){preview_scissor_restore(&surface_scissor);
#ifdef NF_DIAGNOSTIC_SURFACE_CLIP
    NF_DIAGNOSTIC_SURFACE_CLIP(-1);
#endif
    return 0;
   }
   if(preview_world_indices[ring]){model_zero_draws--;world_zero_draws++;}
   if(lit)preview_scissor_run(&surface_scissor,300+column*scale,(end_column-column)*scale);
   glBegin(GL_TRIANGLES);
#ifdef NF_DIAGNOSTIC_ROAD_BOUNDS
   double left,right,top,bottom;int clipped=NF_DIAGNOSTIC_ROAD_BOUNDS(ring,&left,&right,&top,&bottom);
   for(unsigned i=0;i<triangle_count;i+=3){
    if(clipped){RoadVertex polygon[8];unsigned count=road_view_clip_mode(triangles+i,3,polygon,left,right,top,bottom,preview_world_affine[ring]);
     for(unsigned k=1;k+1<count;k++){road_vertex_mode(polygon,preview_world_affine[ring]);road_vertex_mode(polygon+k,preview_world_affine[ring]);road_vertex_mode(polygon+k+1,preview_world_affine[ring]);}}
    else for(unsigned k=0;k<3;k++)road_vertex_mode(triangles+i+k,preview_world_affine[ring]);
   }
#else
   for(unsigned i=0;i<triangle_count;i++)road_vertex_mode(triangles+i,preview_world_affine[ring]);
#endif
   glEnd();model_zero_end(wall_states?wall_states:preview_world_indices[ring]);column=end_column;
  }
  if(lit)preview_scissor_restore(&surface_scissor);
#ifdef NF_DIAGNOSTIC_SURFACE_CLIP
  NF_DIAGNOSTIC_SURFACE_CLIP(-1);
#endif
 } return 1;
}



