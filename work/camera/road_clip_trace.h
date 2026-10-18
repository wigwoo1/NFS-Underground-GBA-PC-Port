#ifndef NF_ROAD_CLIP_TRACE_H
#define NF_ROAD_CLIP_TRACE_H
/* Opt-in diagnostics retain source edges in memory, without timed disk I/O. */
typedef struct {unsigned ring,edge,count,shift,height,affine,crossing;uint64_t identity;int32_t attrs[4],offsets[2];double z0,z1,u,v;NFPoint3 world0,world1,camera0,camera1;} NFRoadClipEdgeTrace;
static NFRoadClipEdgeTrace road_clip_edges[4096];static unsigned road_clip_edge_count;
static void road_clip_trace(unsigned ring,const NFPoint3*world,const RoadVertex*in,const RoadVertex*out,const NFRoadSourceAttributes*raw){
 static int enabled=-1;if(enabled<0)enabled=getenv("NF_CAPTURE_ROAD_EDGES")!=NULL;if(!enabled)return;
 uint64_t identity=14695981039346656037ull;
 const uint8_t*bytes=(const uint8_t*)world;for(size_t i=0;i<raw->count*sizeof(*world);i++){identity^=bytes[i];identity*=1099511628211ull;}
 bytes=(const uint8_t*)raw->attributes;for(size_t i=0;i<raw->count*sizeof(raw->attributes[0]);i++){identity^=bytes[i];identity*=1099511628211ull;}
 unsigned ordinal=0;
 for(unsigned i=0;i<raw->count;i++){
  unsigned previous=(i+raw->count-1)%raw->count;int crossing=(in[previous].p.z<64)!=(in[i].p.z<64);
  if(road_clip_edge_count<4096){NFRoadClipEdgeTrace*r=road_clip_edges+road_clip_edge_count++;*r=(NFRoadClipEdgeTrace){0};r->ring=ring;r->edge=i;r->count=raw->count;r->shift=raw->shift;r->height=raw->stored_height;r->affine=raw->affine;r->crossing=crossing;r->identity=identity;
   memcpy(r->attrs,raw->attributes[previous],8);memcpy(r->attrs+2,raw->attributes[i],8);memcpy(r->offsets,raw->offsets,8);r->z0=in[previous].p.z;r->z1=in[i].p.z;
   r->world0=world[previous];r->world1=world[i];r->camera0=in[previous].p;r->camera1=in[i].p;
   if(crossing){r->u=out[ordinal].u;r->v=out[ordinal].v;}
  }
  if(crossing)ordinal++;if(in[i].p.z>=64)ordinal++;
 }
}
#endif
