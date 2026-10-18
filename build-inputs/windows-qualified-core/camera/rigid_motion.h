#ifndef NF_RIGID_MOTION_H
#define NF_RIGID_MOTION_H
#include <stdint.h>
#define NF_MOTION_API __declspec(dllexport)
typedef struct { double x,y,z; } NFPoint3;
typedef struct { double x,y,z,w; } NFQuaternion;
typedef struct { NFPoint3 position; NFQuaternion rotation; } NFRigidPose;
/* Decode rotation from a column-major Q14 matrix. Position is supplied in
   world units. Small fixed-point scale/shear errors are removed; reflections
   and degenerate matrices fail. Output remains unchanged on failure. */
NF_MOTION_API int nf_pose_decode(const int32_t matrix[12],const NFPoint3*position,NFRigidPose*out);
/* Factor an owned model-to-camera transform into world object pose using
   the same raw world-to-camera record as roads/walls. No emulator writes.
   Both outputs remain unchanged on failure. */
NF_MOTION_API int nf_model_world_pose(const int32_t camera[12],const int32_t model[12],NFRigidPose*camera_pose,NFRigidPose*object_pose);
/* All geometry in one presented scene uses the same alpha. These routines
   never update simulation state. alpha is clamped; non-finite input fails. */
NF_MOTION_API int nf_pose_sample(const NFRigidPose*a,const NFRigidPose*b,double alpha,NFRigidPose*out);
/* Presentation-only owned object record and world Q14 rotation. Replaces only
   Q8 xyz fields12..23; does not write emulator memory. Atomic on rejection. */
NF_MOTION_API int nf_object_pose_sample(const uint8_t object[164],
 const NFRigidPose*a,const NFRigidPose*b,double alpha,
 uint8_t sampled_object[164],int32_t sampled_rotation[12]);
/* Stable object slots; interpolate Q8 xyz and wrapped rotation fields.
   Discrete state/topology comes from older scene until exact newer endpoint.
   Activation/deactivation steps at newer endpoint; changed active descriptor
   or selector rejects atomically. */
NF_MOTION_API int nf_object_pool_sample(const uint8_t*,const uint8_t*,unsigned,double,uint8_t*);
NF_MOTION_API void nf_object_pool_sample_detail(uint32_t[4]);
NF_MOTION_API int nf_object_pool_sample_masked(const uint8_t*,const uint8_t*,unsigned,const uint8_t[32],double,uint8_t*);
/* camera.rotation maps world axes to camera axes; camera.position is the
   world camera position (-translation in the recovered GBA camera record).
   object.rotation maps model axes to world axes. */
NF_MOTION_API int nf_rigid_scene_sample(const NFRigidPose*camera_a,const NFRigidPose*camera_b,
 const NFRigidPose*object_a,const NFRigidPose*object_b,double alpha,
 const NFPoint3*model,unsigned count,NFPoint3*camera_vertices);
#endif
