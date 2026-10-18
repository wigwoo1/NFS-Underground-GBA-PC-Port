#ifndef NF_ROAD_NEAR_CLIP_H
#define NF_ROAD_NEAR_CLIP_H
typedef struct {NFPoint3 p;double u,v;} RoadVertex;
/* Camera-space clipping keeps texture coordinates on the original face. */
static unsigned texture_near_clip(const RoadVertex*in,unsigned count,RoadVertex*out,double near_z){
 unsigned n=0;
 for(unsigned i=0;i<count;i++){
  RoadVertex a=in[(i+count-1)%count],b=in[i];int ai=a.p.z>=near_z,bi=b.p.z>=near_z;
  if(ai!=bi){double t=(near_z-a.p.z)/(b.p.z-a.p.z);out[n++]=(RoadVertex){{a.p.x+(b.p.x-a.p.x)*t,a.p.y+(b.p.y-a.p.y)*t,near_z},a.u+(b.u-a.u)*t,a.v+(b.v-a.v)*t};}
  if(bi)out[n++]=b;
 }return n;
}
#endif
