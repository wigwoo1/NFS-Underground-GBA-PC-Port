#ifndef NF_LIVE_MODEL_INPUTS_API_H
#define NF_LIVE_MODEL_INPUTS_API_H
#include <stdint.h>
#include <stddef.h>
#include "visibility_snapshot.h"
#include "model_outcome.h"
/* Owned original gate results; unknown/conflict never authorize omission. */
__declspec(dllexport) int nf_live_model_outcomes_enable(int);
__declspec(dllexport) NFModelOutcome nf_live_completed_model_outcome_for(uint64_t,uint32_t,uint32_t,uint32_t,const uint32_t[5]);
__declspec(dllexport) void nf_live_model_outcome_stats(uint32_t,uint32_t[4]);
/* Retained complete scenes only, exact epoch/serial/begin/end. Inputs are
   copied: 48-byte signed rotation matrix followed by 512-byte draw palette.
   Object key is the full packet NFI1 model identity (five uint32 words).
   Never substitute the latest draw or another car's palette. Failed calls
   leave outputs untouched; discontinuity/eviction invalidates old identities. */
__declspec(dllexport) int nf_live_completed_models_count(uint64_t,uint32_t,uint32_t,uint32_t,unsigned*);
__declspec(dllexport) int nf_live_completed_model_inputs_for(uint64_t,uint32_t,uint32_t,uint32_t,const uint32_t[5],void*);
/* Native owned endpoint only; no moving-pair substitution. Caller frees the
   validated packet with nf_scene_packet_free. Stage follows native producer. */
__declspec(dllexport) int nf_live_completed_native_multimodel_owned(uint64_t,uint32_t,uint32_t,uint32_t,void**,size_t*,unsigned*);
/* Same endpoint contract, with owned NZI1 original model-index trailers. */
__declspec(dllexport) int nf_live_completed_native_multimodel_indexed_owned(uint64_t,uint32_t,uint32_t,uint32_t,void**,size_t*,unsigned*);
/* Indexed paired generation; missing older model palette accepts only used
   nonzero agreement across its own retained scene banks. Exact row colors
   remain a mandatory consumer dependency for opaque index0. */
__declspec(dllexport) int nf_live_completed_native_multimodel_indexed_pair_packet(const NFVisibilityIdentity*,const NFVisibilityIdentity*,double,void**,size_t*,unsigned*);
/* Complete exact epoch/refresh layer owner; copy160BGR555colors, size320. */
__declspec(dllexport) int nf_layer_queue_zero_colors(uint64_t,unsigned,void*,unsigned);
/* Exact owned render-root data, excluding query-time snapshots and draw overlays. */
__declspec(dllexport) int nf_live_completed_render_read(uint64_t,uint32_t,uint32_t,uint32_t,uint32_t,void*,size_t);
/* Stable object-pool slot; recover only the supported external-pose orientation.
   Position remains in the object record, not rotation matrix scratch words. */
__declspec(dllexport) int nf_live_completed_object_world_rotation(uint64_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,int32_t[12]);
#endif
