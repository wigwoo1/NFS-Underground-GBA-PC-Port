#ifndef NF_PC_SOURCE_SKY_MOTION_H
#define NF_PC_SOURCE_SKY_MOTION_H
#include "source_frame.h"
typedef struct NFPCSkyMotion NFPCSkyMotion;
enum {NFPC_SKY_EXACT_ENDPOINTS=0,NFPC_SKY_CONTINUOUS_PHASE=1};
/* Each source block: NFSK(56), original copied indices(15136), complete owned
   source asset(15376). Owner keys: epoch,serial,begin,end,page. Owns one asset.
   Only verified 240x64,center0 case; transitions/ambiguous turns reject. */
NFPC_API NFPCSkyMotion* nf_pc_sky_motion_decode(const void*,size_t,const uint64_t[5],const void*,size_t,const uint64_t[5],size_t maximum_bytes);
NFPC_API void nf_pc_sky_motion_free(NFPCSkyMotion*);
/* epoch,old/new sky refresh,old/new angle,asset origin,retained bytes */
NFPC_API int nf_pc_sky_motion_info(const NFPCSkyMotion*,uint64_t[7]);
/* Both outputs need15136 bytes and may not overlap. weight is between source
   TEXEL COLORS after palette lookup, never interpolated palette indices.
   Physical destination page switches only at exact new endpoint; display
   footprint is always row44 plus15136bytes (including16-byte final tail).
   Invalid input leaves buffers/weight/destination untouched. Immutable pair is
   safe for independent presentation readers after capture/core destruction.
   No GPU/live timing or full-scene synchronization is implied by this API. */
NFPC_API int nf_pc_sky_motion_sample(const NFPCSkyMotion*,double alpha,unsigned mode,void*lower,size_t,void*upper,size_t,double*weight,uint32_t*destination);
#endif
