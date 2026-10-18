/* Pure decoders/samplers for immutable known-racer source poses.
   Source records stay 1224 bytes; clock is independently owned epoch/serial data. */
#ifndef NF_SOURCE_POSE_SAMPLE_H
#define NF_SOURCE_POSE_SAMPLE_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <math.h>
#include "rigid_motion.h"
#include "object_projection.h"
#ifndef NF_SOURCE_POSE_API
#define NF_SOURCE_POSE_API static
#endif
static uint32_t nf_source_word(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static int nf_source_header(const void*data,size_t bytes,uint64_t meta[16]){
 if(!data||bytes!=1224)return 0;memcpy(meta,data,128);
 return meta[0]&&meta[4]&&meta[2]<=meta[5]&&(!meta[3]||meta[5]<=meta[3])&&meta[11]==31;
}
NF_SOURCE_POSE_API int nf_source_pose_camera(const void*data,size_t bytes,NFRigidPose*out){
 uint64_t meta[16];int32_t matrix[12];
 if(!out||!nf_source_header(data,bytes,meta))return 0;
 memcpy(matrix,(const uint8_t*)data+128,48);
 NFPoint3 position={-(double)matrix[9],-(double)matrix[10],-(double)matrix[11]};
 return nf_pose_decode(matrix,&position,out);
}
typedef struct {const uint8_t*row,*sine;size_t sine_bytes;} NFSourcePoseReader;
static int nf_source_pose_read(void*user,uint32_t address,void*out,size_t bytes){
 const NFSourcePoseReader*r=user;
 if(address==0x03006768u&&bytes==4){memcpy(out,r->row+168,4);return 1;}
 uint32_t external=nf_source_word(r->row+144);
 if(external<=UINT32_MAX-356u&&address>=external+320u&&
    (uint64_t)address+bytes<=(uint64_t)external+356u){memcpy(out,r->row+172+(address-external-320u),bytes);return 1;}
 if(r->sine&&r->sine_bytes==16384&&address>=0x08623700u&&
    (uint64_t)address+bytes<=0x08627700u){memcpy(out,r->sine+(address-0x08623700u),bytes);return 1;}
 return 0;
}
/* Observational candidate; normal-angle results are NOT presentation-verified. */
NF_SOURCE_POSE_API int nf_source_pose_model_matrix(const void*data,size_t bytes,uint32_t address,
 const void*sine,size_t sine_bytes,uint32_t out[12]){
 uint64_t meta[16];if(!out||!nf_source_header(data,bytes,meta))return 0;
 const uint8_t*base=(const uint8_t*)data+176;
 for(unsigned i=0;i<5;i++){
  const uint8_t*p=base+i*208;if(nf_source_word(p)!=address)continue;
  uint32_t camera[12],matrix[12]={0};memcpy(camera,(const uint8_t*)data+128,48);
  NFSourcePoseReader read={p,sine,sine_bytes};
  if(!nf_object_projection_matrix(camera,p+4,matrix,nf_source_pose_read,&read))return 0;
  /* A depth-rejected builder leaves the initial output unchanged. */
  if(!matrix[0]&&!matrix[1]&&!matrix[2])return 0;
  memcpy(out,matrix,48);return 1;
 }
 return 0;
}
NF_SOURCE_POSE_API int nf_source_pose_object(const void*data,size_t bytes,uint32_t address,
 const void*sine,size_t sine_bytes,NFRigidPose*out){
 uint32_t matrix[12];uint64_t meta[16];
 if(!out||!nf_source_header(data,bytes,meta))return 0;
 const uint8_t*verified_row=NULL;
 for(unsigned i=0;i<5;i++){const uint8_t*p=(const uint8_t*)data+176+i*208;if(nf_source_word(p)==address)verified_row=p;}
 if(!verified_row)return 0;
 uint16_t flags;memcpy(&flags,verified_row+14,2);
 /* Only original-matrix-verified external racers are accepted. The angle
    builder below is retained for observational comparison, not presentation. */
 if(!(flags&32)||!nf_source_word(verified_row+168))return 0;
 if(!nf_source_pose_model_matrix(data,bytes,address,sine,sine_bytes,matrix))return 0;
 int32_t camera[12];memcpy(camera,(const uint8_t*)data+128,48);
 NFRigidPose cp,op;
 if(!nf_model_world_pose(camera,(const int32_t*)matrix,&cp,&op))return 0;
 const uint8_t*base=(const uint8_t*)data+176;
 for(unsigned i=0;i<5;i++){
  const uint8_t*p=base+i*208;if(nf_source_word(p)!=address)continue;
  int32_t xyz[3];memcpy(xyz,p+16,12);
  op.position=(NFPoint3){xyz[0]/256.0,xyz[1]/256.0,xyz[2]/256.0};
  *out=op;return 1;
 }
 return 0;
}
/* Returns a strict interpolation phase from actual original source times.
   Never substitutes integer flip timestamps, clamps or extrapolates. */
NF_SOURCE_POSE_API int nf_source_pose_phase(const void*older,size_t older_size,const uint64_t older_clock[3],
 const void*newer,size_t newer_size,const uint64_t newer_clock[3],double target,double*out){
 uint64_t a[16],b[16];
 if(!out||!older_clock||!newer_clock||!isfinite(target)||
    !nf_source_header(older,older_size,a)||!nf_source_header(newer,newer_size,b)||
    a[0]!=b[0]||a[1]>=b[1]||a[6]!=b[6]||a[7]!=b[7]||a[8]!=b[8]||
    older_clock[0]!=a[4]||older_clock[1]!=a[5]||older_clock[2]>=280896||
    newer_clock[0]!=b[4]||newer_clock[1]!=b[5]||newer_clock[2]>=280896||
    older_clock[0]>=newer_clock[0]||older_clock[1]>newer_clock[1])return 0;
 uint64_t tick_delta=newer_clock[0]-older_clock[0];
 int64_t phase_delta=(int64_t)((newer_clock[1]-older_clock[1])*280896u)+
     (int64_t)newer_clock[2]-(int64_t)older_clock[2];
 if(phase_delta<=0||(uint64_t)phase_delta!=tick_delta)return 0;
 double lo=older_clock[1]+older_clock[2]/280896.0;
 double hi=newer_clock[1]+newer_clock[2]/280896.0;
 if(!(lo<=target&&target<=hi)||!(lo<hi))return 0;
 double alpha=(target-lo)/(hi-lo);if(!isfinite(alpha)||alpha<0||alpha>1)return 0;
 *out=alpha;return 1;
}
#endif
