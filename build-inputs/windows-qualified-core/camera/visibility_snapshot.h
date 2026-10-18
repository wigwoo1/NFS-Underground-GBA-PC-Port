#ifndef NF_VISIBILITY_SNAPSHOT_H
#define NF_VISIBILITY_SNAPSHOT_H
#include "native_visibility.h"
#include "scene_command_plan.h"
#include "native_surface.h"
/* Explicit owner-core capture setting; no environment dependency in apps. */
__declspec(dllexport) void nf_visibility_snapshot_owned_callbacks(int);
/* Opt-in NF_TRACE_NATIVE_COMMANDS diagnostic: count/queue_count words,
   queue records then 16-word command rows(kind,owner,pass,mask,object,source,
   four bounds,four record words,two viewport words). Borrowed copy only. */
__declspec(dllexport) size_t nf_visibility_snapshot_command_trace(void*,size_t);
/* Same opt-in diagnostic: NQF1/state_address/selected/recovery,26 pose words,
   then owned EWRAM+IWRAM. For independent original-routine replay only. */
__declspec(dllexport) size_t nf_visibility_snapshot_query_fixture(void*,size_t);
typedef struct NFVisibilityAssets NFVisibilityAssets;
typedef struct NFVisibilitySnapshot NFVisibilitySnapshot;
__declspec(dllexport) int nf_visibility_snapshot_attach_query(NFVisibilitySnapshot*,const uint32_t[2],const uint32_t[12]);
__declspec(dllexport) int nf_visibility_snapshot_owned_query(const NFVisibilitySnapshot*,uint32_t[14]);
/* Presentation-owned projection clone; source snapshot remains immutable. */
__declspec(dllexport) NFVisibilitySnapshot* nf_visibility_snapshot_clone_focal(const NFVisibilitySnapshot*,uint32_t);
__declspec(dllexport) int nf_visibility_snapshot_prepared_builder_commands_focal(NFVisibilitySnapshot*,NFVisibilitySnapshot*,const uint32_t[12],uint32_t,uint32_t,uint32_t,const uint8_t*,NFNativeSceneCommand*,unsigned,unsigned*);
typedef struct NFVisibilityHistory NFVisibilityHistory;
typedef struct {uint8_t state[256],queue[NF_VISIBILITY_QUEUE_BYTES],groups[4096];uint32_t selected;} NFVisibilityResult;
typedef struct {uint64_t epoch;uint32_t serial,begin_refresh,end_refresh,query_refresh,builder_refresh;} NFVisibilityIdentity;
typedef struct {uint32_t base[2],query[12],view[12];} NFVisibilityPoseInputs;
__declspec(dllexport) int nf_visibility_snapshot_query_sample(const NFVisibilitySnapshot*,const NFVisibilitySnapshot*,double,NFVisibilityPoseInputs*);
__declspec(dllexport) int nf_projection_focal_sample(const uint32_t[2],const uint32_t[2],double,uint32_t[2]);
/* Single-owner lifetime operations, not thread-safe. Assets own one ROM copy
   (at most 32 MiB), shared by refcount with all snapshots. No borrowed buffers. */
__declspec(dllexport) NFVisibilityAssets* nf_visibility_assets_create(const void*rom,size_t size);
__declspec(dllexport) void nf_visibility_assets_release(NFVisibilityAssets*);
/* ram is exactly EWRAM[0x40000] followed by IWRAM[0x8000]. Each snapshot owns
   that copy plus both matrices and query inputs. This is visibility data only,
   not a complete render packet. Caller ensures scene/epoch coherence. */
/* Owned original builder-entry list; has a view matrix, no query pose.
   evaluate/evaluate_for use native builder; query pose/interpolation reject. */
__declspec(dllexport) NFVisibilitySnapshot* nf_visibility_snapshot_create_prepared(NFVisibilityAssets*,const void*,size_t,uint32_t,uint32_t);
__declspec(dllexport) int nf_visibility_snapshot_prepared_view(const NFVisibilitySnapshot*,uint32_t out[12]);
/* Rebuild owned prepared list with an explicit actual view only. Does not
   recover/re-query list coverage. Identity mismatch rejects atomically. */
__declspec(dllexport) int nf_visibility_snapshot_evaluate_prepared_view(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const uint32_t view[12],NFVisibilityResult*);
/* Actual view matrices only: rigid rotation interpolation and linear source
   translation. No race-query/base inputs are synthesized. */
__declspec(dllexport) int nf_visibility_view_sample(const uint32_t[12],const uint32_t[12],double,uint32_t out[12]);
__declspec(dllexport) NFVisibilitySnapshot* nf_visibility_snapshot_create(NFVisibilityAssets*,const void*ram,size_t size,uint32_t state_address,uint32_t selected,uint32_t recovery,const uint32_t base[2],const uint32_t query[12],const uint32_t view[12]);
/* Owned clone, sharing only immutable reference-counted ROM assets. */
__declspec(dllexport) NFVisibilitySnapshot* nf_visibility_snapshot_clone(const NFVisibilitySnapshot*);
__declspec(dllexport) void nf_visibility_snapshot_destroy(NFVisibilitySnapshot*);
/* Optional owned BG palette (512 bytes at05000000). Set exactly once before
   identity binding; caller must capture it coherently with scene assets.
   Absent palette ranges fail reads; this does not make a full render snapshot. */
__declspec(dllexport) int nf_visibility_snapshot_set_palette(NFVisibilitySnapshot*,const void*palette,size_t size);
__declspec(dllexport) int nf_visibility_snapshot_read(NFVisibilitySnapshot*,uint32_t address,void*out,size_t size);
/* Evaluation is repeatable and leaves snapshot and output unchanged on error. */
__declspec(dllexport) int nf_visibility_snapshot_evaluate(NFVisibilitySnapshot*,NFVisibilityResult*out);
/* Bind once before publication. Caller supplies verified packet/capture identity;
   bounds must enclose ordered query/builder timestamps. Untagged snapshots and
   mismatched epoch/scene/bounds cannot be evaluated through the checked API. */
__declspec(dllexport) int nf_visibility_snapshot_bind(NFVisibilitySnapshot*,const NFVisibilityIdentity*);
__declspec(dllexport) int nf_visibility_snapshot_evaluate_for(NFVisibilitySnapshot*,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,NFVisibilityResult*out);
/* Checked copy of retained inputs; output remains unchanged on mismatch. */
__declspec(dllexport) int nf_visibility_snapshot_pose(NFVisibilitySnapshot*,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,NFVisibilityPoseInputs*out);
/* Explicit pose override; never interpolates screen polygons or mutates the
   retained scene. Caller supplies mutually coherent base/query/view inputs. */
__declspec(dllexport) int nf_visibility_snapshot_evaluate_at(NFVisibilitySnapshot*,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,const NFVisibilityPoseInputs*,NFVisibilityResult*out);
/* Planar research adapter: exact endpoints, coherent transposed rotations and
   Q8 base translation. Rejects unsupported inputs and leaves output unchanged. */
__declspec(dllexport) int nf_visibility_pose_sample(const NFVisibilityPoseInputs*,const NFVisibilityPoseInputs*,double alpha,NFVisibilityPoseInputs*out);
typedef struct {uint8_t state[256],record[16],edges[32*52],stream[64*24];} NFVisibilityRegionResult;
/* Re-evaluates queue, selects its exact ordinal (including repeated regions),
   then reconstructs with the same pose. Success=1; all failures leave output intact. */
__declspec(dllexport) int nf_visibility_snapshot_region_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,unsigned ordinal,NFVisibilityRegionResult*out);
typedef struct {uint32_t source,pass;NFVisibilityWallDraw draw;} NFSampledWallDraw;
typedef struct {uint32_t count;uint8_t record[16];NFSampledWallDraw draws[64];} NFSampledWallPlan;
/* Owned value output; queue regions only. Merged records yield an empty plan. */
__declspec(dllexport) int nf_visibility_snapshot_wall_plan(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,unsigned,NFSampledWallPlan*);
/* Caller supplies scene-coherent owned draw state/object; does not select object eligibility. */
__declspec(dllexport) int nf_visibility_snapshot_object_plan(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,const uint8_t state[256],const uint8_t object[164],NFSampledWallPlan*);
typedef struct {uint32_t count;NFSampledWallPlan plans[NF_VISIBILITY_QUEUE_CAPACITY];} NFSampledQueuePlans;
/* One visibility evaluation, queue-index order, atomic owned value output. */
__declspec(dllexport) int nf_visibility_snapshot_queue_plans(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,NFSampledQueuePlans*);
/* History owns copies, at most 16, and counts its object, one shared ROM asset
   allocation and its snapshot copies against budget. External snapshots and
   temporary incoming clone allocation are excluded. No borrowed entries. */
__declspec(dllexport) size_t nf_visibility_history_budget(NFVisibilityAssets*,unsigned count);
__declspec(dllexport) NFVisibilityHistory* nf_visibility_history_create(NFVisibilityAssets*,size_t budget);
__declspec(dllexport) int nf_visibility_history_push(NFVisibilityHistory*,const NFVisibilitySnapshot*);
__declspec(dllexport) int nf_visibility_history_evaluate(NFVisibilityHistory*,uint64_t epoch,uint32_t serial,uint32_t begin_refresh,uint32_t end_refresh,NFVisibilityResult*out);
__declspec(dllexport) size_t nf_visibility_history_bytes(const NFVisibilityHistory*);
__declspec(dllexport) void nf_visibility_history_destroy(NFVisibilityHistory*);
/* Identity-checked owned visibility/commands/assets packet. Optional copied object pool supplies coherent sampled object poses; NULL uses retained objects. Callbacks changing the sampled camera matrix reject the packet. Snapshot immutable; output publication atomic. */
__declspec(dllexport) int nf_visibility_snapshot_packet_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFSceneObjectCallback,void*,void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_palettes_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFSceneObjectCallback,void*,NFScenePalette,void*,void**,size_t*);
/* Owned selector12 callback and projection scratch. Other selectors reject.
   Render resampling suppresses sound delivery; never mutates simulation state. */
__declspec(dllexport) int nf_visibility_snapshot_packet_native_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_palettes_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,void**,size_t*);
/* Single-owner last attempt: stage,commands,models,billboards,secondary roads,native callback calls. */
__declspec(dllexport) void nf_visibility_snapshot_packet_detail(uint32_t[6]);
/* Multi-car native callbacks and exact per-command rotation/palette resolver. */
__declspec(dllexport) int nf_visibility_snapshot_packet_native_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,NFSceneModelInputs,void*,void**,size_t*);
/* Opt-in NZI1 model texture indices from the retained scene reader. */
__declspec(dllexport) int nf_visibility_snapshot_packet_native_indexed_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,NFSceneModelInputs,void*,void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_indexed_world_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,NFSceneModelInputs,void*,void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_classified_world_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,NFSceneModelInputs,void*,void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_road_attributes_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,NFSceneModelInputs,void*,void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_classified_assets_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePaletteAssets,void*,NFSceneModelInputs,void*,void**,size_t*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_road_attributes_assets_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePaletteAssets,void*,NFSceneModelInputs,void*,void**,size_t*);
/* Explicit prepared view-only classified asset packet path. */
__declspec(dllexport) int nf_visibility_snapshot_packet_prepared_assets_models(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const uint32_t[12],double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePaletteAssets,void*,NFSceneModelInputs,void*,unsigned,void**,size_t*);
/* Owned root command reconstruction; required object callbacks reject. */
__declspec(dllexport) int nf_visibility_snapshot_prepared_builder_commands(NFVisibilitySnapshot*,NFVisibilitySnapshot*,NFNativeSceneCommand*,unsigned,unsigned*);
__declspec(dllexport) int nf_visibility_snapshot_prepared_captured_commands(NFVisibilitySnapshot*,NFNativeSceneCommand*,unsigned,unsigned*);
__declspec(dllexport) int nf_visibility_snapshot_prepared_commands(NFVisibilitySnapshot*,NFNativeSceneCommand*,unsigned,unsigned*);
/* Re-evaluate retained prepared root/builder at an explicit actual view.
   Neither retained snapshot is mutated; output atomic on topology/evaluation failure. */
__declspec(dllexport) int nf_visibility_snapshot_prepared_builder_commands_view(NFVisibilitySnapshot*,NFVisibilitySnapshot*,const uint32_t[12],NFNativeSceneCommand*,unsigned,unsigned*);
__declspec(dllexport) int nf_visibility_snapshot_prepared_builder_commands_object(NFVisibilitySnapshot*,NFVisibilitySnapshot*,const uint32_t[12],uint32_t,const uint8_t[164],NFNativeSceneCommand*,unsigned,unsigned*);
__declspec(dllexport) int nf_visibility_snapshot_packet_native_road_camera_model_inputs_at(NFVisibilitySnapshot*,uint64_t,uint32_t,uint32_t,uint32_t,const NFVisibilityPoseInputs*,double,uint32_t,const uint8_t*,unsigned,const int32_t[12],NFScenePalette,void*,NFSceneModelInputs,void*,void**,size_t*);
#endif

