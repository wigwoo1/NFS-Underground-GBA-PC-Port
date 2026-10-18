#ifndef NF_PC_SCENE_POSE_SAMPLE_H
#define NF_PC_SCENE_POSE_SAMPLE_H
#include "source_scene.h"
#include "model_mesh.h"
#include "world_mesh.h"
#include "world_motion_owner.h"
/* Component mesh samplers from prepared-motion scenes. Requires unique copied
   original identities within each selected source owner, sameepoch, forward
   global gap<=8 and held/forward source owner times. No order/polygon matching.
   Model local geometry/UV and world source points/UV are validated by existing
   samplers. Fixed-camera world records still reject. Held sources select exact
   older pose/material until alpha1. Results own buffers, outlive scenes/core.
   Caller still MUST apply source command scissor/order and region clipping;
   model mesh decode uses standalone layout defaults. No complete scene/HUD/sky
   or visibility interpolation, and no live renderer integration implied. */
NFPC_API NFPCModelMesh* nf_pc_scene_model_pose(const NFPCScene*,unsigned,const NFPCScene*,unsigned,double,size_t);
NFPC_API NFPCWorldMesh* nf_pc_scene_world_pose(const NFPCScene*,unsigned,const NFPCScene*,unsigned,double,size_t);
/* Forward source-owner batch, alpha<1. Holds copied original source worlds
   and one sampled camera clone. Use class_mesh per older surface to preserve
   duplicate calls without selecting a newer counterpart. Held bands keep the
   older endpoint directly; alpha1 submits the full newer endpoint separately. */
NFPC_API NFPCWorldMotionOwner* nf_pc_scene_world_pose_owner(const NFPCScene*,unsigned older_owner,const NFPCScene*,unsigned newer_owner,double,size_t);
/* Camera-capture-time fraction for a forward source-owner pair. Physical
   owner identity remains separate. Requires copied timing metadata, sameepoch,
   forward global/owner gaps<=8 and target within the measured camera bracket.
   Held owners reject; caller must handle held regions explicitly. Exact alpha1
   selects complete new endpoint. Not per-model rotation/HUD synchronization.
   Invalid inputs leave alpha untouched; no core/frame dependency. */
NFPC_API int nf_pc_scene_pose_alpha(const NFPCScene*,unsigned,const NFPCScene*,unsigned,double target,double*alpha);
#endif
