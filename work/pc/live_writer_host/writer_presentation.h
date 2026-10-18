#ifndef NF_PC_WRITER_PRESENTATION_H
#define NF_PC_WRITER_PRESENTATION_H
#include "writer_physical_support.h"
typedef struct NFPCWriterPresentation NFPCWriterPresentation;
/* Own native endpoint scene, physical supports and copied owner camera records.
   One retained budget includes all three and native constructor peak. Existing
   bounded decode/partition/lookup/geometry scratch, GPU and RSS are excluded.
   Inputs borrowed only during prepare. No core callbacks. */
NFPC_API NFPCWriterPresentation*nf_pc_writer_presentation_prepare(const NFPCSourceFrame*,const NFRecipeSnapshot*const[2],const uint64_t cameras[2][16],size_t maximum);
NFPC_API void nf_pc_writer_presentation_free(NFPCWriterPresentation*);
/* epoch,refresh,owners,regions,bindings,total retained,native retained,
   support retained,constructor peak,root bytes */
NFPC_API int nf_pc_writer_presentation_info(const NFPCWriterPresentation*,uint64_t out[10]);
NFPC_API int nf_pc_writer_presentation_camera(const NFPCWriterPresentation*,unsigned,uint64_t out[16],NFRigidPose*);
NFPC_API int nf_pc_writer_presentation_region(const NFPCWriterPresentation*,size_t,uint64_t out[12]);
/* Borrowed region binding valid until presentation free. */
NFPC_API int nf_pc_writer_presentation_binding(const NFPCWriterPresentation*,size_t,const NFPCRecipeWriter**,const NFPCWriterAddressMap**);
/* Paired sampling does not establish new visibility/occlusion. Explicit owner
   indices must match a region's captured key. Epoch/projection/gap guards apply;
   newer coverage unavailable before alpha1. Atomic rejection. */
NFPC_API int nf_pc_writer_presentation_pair_ring(const NFPCWriterPresentation*,unsigned,const NFPCWriterPresentation*,unsigned,unsigned coverage_side,size_t,double,void*,size_t,unsigned*);
/* Unchanged integer endpoint composition, not a fractional full-scene API. */
NFPC_API int nf_pc_writer_presentation_draw(NFPCSceneGPU*,NFPCWriterPresentation*,unsigned,unsigned,unsigned,unsigned,void*,size_t);
NFPC_API int nf_pc_writer_presentation_render(NFPCSceneGPU*,NFPCWriterPresentation*,unsigned,unsigned,unsigned,unsigned);
/* Borrowed read-only physical support, valid until presentation free. */
NFPC_API const NFPCWriterPhysicalSupport*nf_pc_writer_presentation_support(const NFPCWriterPresentation*);
#endif
