#ifndef NF_ROAD_NEAR_CONTINUITY_H
#define NF_ROAD_NEAR_CONTINUITY_H
/* Continuous presentation policy: remove the biased front-on-plane UV gap.
   Source game state is unchanged. This intentionally differs from the original
   biased generated attribute when an edge's front depth is exactly64. */
static int road_near_front_limit(const RoadVertex*in,unsigned count,RoadVertex*out,unsigned n,const NFRoadSourceAttributes*raw,const uint32_t*table,unsigned*adjusted){
 if(!in||!out||!raw||!table||!adjusted||count<3||count>32||raw->count!=count||raw->shift>10||raw->stored_height<2||(raw->stored_height&1)||raw->affine>1||n>64)return 0;
 RoadVertex staged[64];memcpy(staged,out,n*sizeof(*out));unsigned ordinal=0,changes=0;
 double offset[2]={raw->offsets[0]/(256.0*(1u<<raw->shift)),raw->offsets[1]/(256.0*raw->stored_height)};
 for(unsigned i=0;i<count;i++){
  unsigned previous=(i+count-1)%count;int ai=in[previous].p.z>=64,bi=in[i].p.z>=64;
  if(ai!=bi){if(ordinal>=n)return 0;unsigned front=ai?previous:i;double depth=in[front].p.z;
   if(depth<65){double uv[2],weight=depth-64;if(!nf_road_vertex_attributes(64,raw->attributes[front],raw->shift,raw->stored_height,raw->affine,table,uv))return 0;
    staged[ordinal].u=(uv[0]+offset[0])*(1-weight)+staged[ordinal].u*weight;staged[ordinal].v=(uv[1]+offset[1])*(1-weight)+staged[ordinal].v*weight;changes++;
   }ordinal++;
  }if(bi)ordinal++;
 }if(ordinal!=n)return 0;memcpy(out,staged,n*sizeof(*out));*adjusted=changes;return 1;
}
static int texture_near_clip_continuous(const RoadVertex*in,unsigned count,RoadVertex*out,const NFRoadSourceAttributes*raw,const uint32_t*table,unsigned*out_count,unsigned*adjusted){
 if(!out||!out_count||!adjusted)return 0;
 RoadVertex staged[64];unsigned n,changes;
 if(!texture_near_clip_corrected(in,count,staged,64,raw,table,&n)||!road_near_front_limit(in,count,staged,n,raw,table,&changes))return 0;
 memcpy(out,staged,n*sizeof(*out));*out_count=n;*adjusted=changes;return 1;
}
#endif
