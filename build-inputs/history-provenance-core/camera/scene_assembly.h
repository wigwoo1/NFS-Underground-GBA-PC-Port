#ifndef NF_SCENE_ASSEMBLY_H
#define NF_SCENE_ASSEMBLY_H
#include "scene_packet.h"
#include "native_surface.h"
typedef struct NFSceneAssembly NFSceneAssembly;
__declspec(dllexport) void nf_assembly_asset_stats(uint64_t[2]);
__declspec(dllexport) int nf_assembly_commands_classified_assets_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePaletteAssets,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
__declspec(dllexport) int nf_assembly_commands_road_attributes_assets_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePaletteAssets,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);

/* Multi-model native command path. Resolve each model's exact identity to
   copied rotation/palette; failure rejects the entire scene atomically. */
__declspec(dllexport) int nf_assembly_commands_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
/* Opt-in original model-index NZI1 trailers from the same owned scene reader. */
__declspec(dllexport) int nf_assembly_commands_indexed_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
/* Explicit original primary-road indices plus model indices. */
__declspec(dllexport) int nf_assembly_commands_indexed_world_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
/* Explicit wall skip/write-zero classifications plus road/model indices.
   Requires a consumer supporting all wall lighting planes. */
__declspec(dllexport) int nf_assembly_commands_classified_world_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
__declspec(dllexport) int nf_assembly_commands_road_attributes_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
__declspec(dllexport) void nf_assembly_detail(const NFSceneAssembly*,uint32_t out[5]);
/* One owner, one complete source scene. Append in original drawing order.
   Inputs are copied. Any append failure poisons this scene until reset.
   Legacy default supports one model; explicit opt-in supports up to16. */
__declspec(dllexport) NFSceneAssembly* nf_assembly_create(void);
/* Configure an empty owner only; reset preserves this setting. Consumers must
   support NSP2 before enabling multiple models in live production. */
__declspec(dllexport) int nf_assembly_multimodel(NFSceneAssembly*,int);
__declspec(dllexport) void nf_assembly_reset(NFSceneAssembly*);
__declspec(dllexport) void nf_assembly_destroy(NFSceneAssembly*);
__declspec(dllexport) int nf_assembly_surface(NFSceneAssembly*,const uint32_t identity[5],const void*,size_t,const void*lighting,size_t);
/* Copy original indices for an appended unlit road; append-order index.
   Failure poisons the scene; ownership survives caller changes until reset. */
__declspec(dllexport) int nf_assembly_surface_indices(NFSceneAssembly*,unsigned,const uint8_t*,size_t);
__declspec(dllexport) int nf_assembly_road_attributes(NFSceneAssembly*,unsigned,const NFRoadSourceAttributes*);
__declspec(dllexport) int nf_assembly_road_mapping(NFSceneAssembly*,unsigned,unsigned);
__declspec(dllexport) int nf_assembly_wall_states(NFSceneAssembly*,unsigned,const uint8_t*,size_t,unsigned);
__declspec(dllexport) int nf_assembly_wall_indices(NFSceneAssembly*,unsigned,const uint8_t*,const uint8_t*,size_t,unsigned);
__declspec(dllexport) int nf_assembly_model_bounds(NFSceneAssembly*,unsigned,const uint16_t[4]);
__declspec(dllexport) int nf_assembly_model(NFSceneAssembly*,const uint32_t identity[5],const void*,size_t);
/* Optional per-surface copied bounds, index in append order. All surfaces
   require bounds at one sampled alpha once enabled; failures poison scene. */
__declspec(dllexport) int nf_assembly_bounds(NFSceneAssembly*,unsigned,double,const uint16_t[4]);
/* Output remains unchanged on failure. Successful finish retains source data
   until reset; release the returned packet with nf_scene_packet_free. */
__declspec(dllexport) int nf_assembly_finish(NFSceneAssembly*,uint32_t serial,uint32_t begin,uint32_t end,uint32_t page,const void*reciprocals,size_t,void**,size_t*);
/* Bounded all-or-nothing native command assets/lighting assembly. Identities are supplied by the scene owner. NULL bounds uses owned command bounds. */
__declspec(dllexport) int nf_assembly_commands(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,const uint8_t[512],const int32_t[12],uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
__declspec(dllexport) int nf_assembly_commands_palettes(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
__declspec(dllexport) int nf_assembly_road_camera(NFSceneAssembly*,unsigned,const NFRoadCameraMetadata*);
__declspec(dllexport) int nf_assembly_commands_road_camera_model_inputs(const NFNativeSceneCommand*,unsigned,const uint32_t*,const uint16_t*,double,NFReadMemory,void*,NFScenePalette,void*,const int32_t[12],NFSceneModelInputs,void*,uint32_t,uint32_t,uint32_t,uint32_t,const void*,void**,size_t*);
#endif

