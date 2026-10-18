#ifndef NF_NATIVE_SURFACE_H
#define NF_NATIVE_SURFACE_H
#include <stdint.h>
#include <stddef.h>
#include "scene_command_plan.h"
#include "draw_palette.h"
typedef int (*NFReadMemory)(void*context,uint32_t address,void*out,size_t size);
/* Owned source UV policy inputs, no borrowed memory or visibility claim.
   Source edge order retained; unused attribute entries are zero. Animation
   signed offsets stay separate from fixed14 source attributes. */
#include "road_source_attributes.h"
__declspec(dllexport) int nf_road_source_attributes_layer_owned(NFReadMemory,void*,uint32_t,uint32_t,unsigned,unsigned,NFRoadSourceAttributes*);
__declspec(dllexport) int nf_road_source_attributes_owned(NFReadMemory,void*,uint32_t,uint32_t,unsigned,NFRoadSourceAttributes*);
__declspec(dllexport) int nf_scene_command_road_attributes_owned(const NFNativeSceneCommand*,NFReadMemory,void*,NFRoadSourceAttributes*);
/* Exact consumed-input check; scratch is temporary, consumed bytes remain unchanged. */
__declspec(dllexport) int nf_memory_read_matches(NFReadMemory,void*,uint32_t,const void*,size_t,void*,size_t);
/* Wall classifications owned by caller: base plane then 16 shaded planes for
   lit material, base only for unlit. 0 skip,1 write index0,2 write nonzero.
   Material uses original wall layout; all outputs unchanged on failure. */
__declspec(dllexport) int nf_wall_write_states_owned(NFReadMemory,void*,uint32_t,unsigned,uint8_t**,uint32_t*,uint32_t*,uint32_t*);
/* Same owned plane layout, exact output indices instead of classifications.
   Source-index0 remains skip; consult separate states to distinguish skip/write0. */
__declspec(dllexport) int nf_wall_output_indices_owned(NFReadMemory,void*,uint32_t,unsigned,uint8_t**,uint32_t*,uint32_t*,uint32_t*);
__declspec(dllexport) int nf_scene_command_wall_indices_owned(const NFNativeSceneCommand*,NFReadMemory,void*,uint8_t**,uint32_t*,uint32_t*,uint32_t*);
__declspec(dllexport) int nf_scene_command_wall_states_owned(const NFNativeSceneCommand*,NFReadMemory,void*,uint8_t**,uint32_t*,uint32_t*,uint32_t*);
/* Owned original model texel indices, including opaque index zero.
   Caller frees returned bytes; dimensions and pointer unchanged on failure.
   Intended to retain display-dependent index metadata beside native geometry. */
__declspec(dllexport) int nf_model_texture_indices_owned(NFReadMemory,void*,const uint8_t model_context[68],uint8_t**,uint32_t*,uint32_t*);
/* Original80233E0 external-pose branch only (global03006768 nonzero).
   Reads object+140 pose reference and nine Q12 words at+320; wrapping Q14
   conversion, zero rotation translation. Unsupported branch rejects atomically. */
__declspec(dllexport) int nf_model_world_rotation_owned(NFReadMemory,void*,const uint8_t[164],int32_t[12]);
/* Source hidden bit is replaced by an override material's bit when present.
   Returns 1 with visible=0/1, or 0 on unavailable data, leaving output intact. */
__declspec(dllexport) int nf_wall_visibility_flag(NFReadMemory,void*context,const uint8_t state[256],const uint8_t source[68],int*visible);
/* Bounded region-table ownership lookup. Requires exactly one valid owner;
   failure leaves descriptor unchanged. Does not establish visibility. */
__declspec(dllexport) int nf_wall_owner(NFReadMemory,void*context,uint32_t state,uint32_t source,uint32_t*descriptor);
/* Unlit indexed texture only. Compare every used index across contiguous
   512-byte palettes, including index zero; copy first palette on agreement.
   Unused entries are not guaranteed interchangeable. Atomic on failure. */
__declspec(dllexport) int nf_candidate_palette(const uint8_t*indices,size_t pixels,const uint8_t*palettes,unsigned count,uint8_t out[512]);
/* Unlit wall-specific policy: index zero is transparent; every used nonzero
   index must agree. Generic candidate_palette still compares index zero. */
__declspec(dllexport) int nf_wall_candidate_palette(const uint8_t*,size_t,const uint8_t*,unsigned,uint8_t out[512]);
/* Opaque models with retained NZI1 metadata: index0 must be colored separately
   from exact display rows. Every used nonzero index must agree across banks. */
__declspec(dllexport) int nf_model_display_palette(const uint8_t*,size_t,const uint8_t*,unsigned,uint8_t out[512]);
/* Caller supplies one coherent owned scene reader and its retained palettes.
   Unlit default-UV wall only; outputs are caller-owned, atomic on failure.
   This extracts a supplied source identity, not candidate visibility. */
__declspec(dllexport) int nf_extract_wall_candidate(NFReadMemory,void*context,uint32_t state,uint32_t source,const uint8_t*palettes,unsigned count,void**surface,size_t*size);
/* Diagnostic stage: 0 success,1 input/owner,2 flags/visibility,3 base animation,
   4 resolved material,5 dimensions/allocation,6 texture read,7 palette agreement,
   8 surface extraction. Surface outputs retain the original atomic contract. */
__declspec(dllexport) int nf_extract_wall_candidate_diagnostic(NFReadMemory,void*,uint32_t,uint32_t,const uint8_t*,unsigned,void**,size_t*,unsigned*);
/* Descriptor+8 road material selection only; does not establish eligibility.
   Output: resolved descriptor,animation record,texture,shift,stored height. */
/* Layer0 primary descriptor+8, layer1 optional second material descriptor+4. */
__declspec(dllexport) int nf_road_material_plan_layer(NFReadMemory,void*,uint32_t,uint32_t,unsigned,uint32_t out[5]);
__declspec(dllexport) int nf_road_material_plan(NFReadMemory,void*,uint32_t,uint32_t,uint32_t out[5]);
/* Conservative primary-road extraction; all used opaque texel indices,
   including zero, must agree across supplied coherent scene palettes. */
__declspec(dllexport) int nf_extract_road_candidate_layer(NFReadMemory,void*,uint32_t,uint32_t,const uint8_t*,unsigned,unsigned,void**,size_t*);
__declspec(dllexport) int nf_extract_road_candidate(NFReadMemory,void*,uint32_t,uint32_t,const uint8_t*,unsigned,void**,size_t*);
/* Construct one RFD1 surface record (without the section header) from game
   memory at the road draw entry. Only the verified +08 branch is supported.
   Reader must reject unavailable ranges. Outputs remain unchanged on failure. */
__declspec(dllexport) int nf_extract_road_layer(NFReadMemory,void*,uint32_t,uint32_t,uint32_t,uint32_t,unsigned,void**,size_t*);
__declspec(dllexport) int nf_extract_road(NFReadMemory,void*context,uint32_t state,uint32_t descriptor,uint32_t material,uint32_t uv,void**out,size_t*size);
/* Default vertical-UV walls. Returns one surface and its NFL1 lighting record.
   world_descriptor supplies cyclic endpoint ownership; resolved_material is
   the game's selected animation-frame descriptor. Extended UV mode fails. */
__declspec(dllexport) int nf_extract_wall(NFReadMemory,void*context,uint32_t state,uint32_t world_descriptor,uint32_t source,uint32_t material,uint32_t resolved_material,uint32_t flags,void**surface,size_t*surface_size,void**lighting,size_t*lighting_size);
__declspec(dllexport) int nf_extract_model(NFReadMemory,void*context,uint32_t model_context,uint32_t camera,uint32_t object,const int32_t object_rotation[12],void**out,size_t*size);
/* NFB1 captured-pose billboard: header magic,width,height,reserved (16),
   rect L,T,R,B (16), UV origin/extents (16), bounds L,R,T,B u16 (8), RGBA.
   Standalone owned diagnostic record; not yet an NSP1 section or pose model. */
__declspec(dllexport) int nf_extract_billboard(NFReadMemory,void*context,uint32_t draw_context,uint32_t state,void**out,size_t*size);
typedef struct {
 uint32_t width,height;int32_t rectangle[4];uint32_t uv[4];uint16_t bounds[4];const uint8_t*rgba;
} NFBillboardView;
/* Borrowed view; caller keeps record alive. Reject unsupported UV ranges,
   reversed rectangles/viewports and non-exact payload lengths atomically. */
__declspec(dllexport) int nf_billboard_view(const void*data,size_t size,NFBillboardView*out);
/* Continuous clipped quad, clockwise TL/TR/BR/BL x,y,u,v. Maps source
   240x160 to target extent; caller chooses aspect-correct target/letterbox.
   Returns 1 visible,0 outside,-1 invalid. Captured pose only. */
__declspec(dllexport) int nf_billboard_quad(const void*data,size_t size,uint32_t target_width,uint32_t target_height,double out[16]);
__declspec(dllexport) void nf_surface_free(void*);
/* Owned original primary-road indices using command-owned state overlay. */
__declspec(dllexport) int nf_scene_command_road_indices_owned(const NFNativeSceneCommand*,NFReadMemory,void*,uint8_t**,uint32_t*,uint32_t*);
/* Extract owned world/model asset directly from native leaf command. Current
   world policy: primary roads, default-UV unlit walls and supplied coherent
   palette. Model rotation supplied from retained pose. Unsupported leaves
   reject atomically; no original draw-entry/context memory is required. */
__declspec(dllexport) int nf_extract_scene_command(const NFNativeSceneCommand*,NFReadMemory,void*,const uint8_t palette[512],const int32_t rotation[12],void**,size_t*,unsigned*);
/* Complete wall surface plus owned lighting; other supported kinds return no lighting. All four outputs publish atomically. */
__declspec(dllexport) int nf_extract_scene_command_full(const NFNativeSceneCommand*,NFReadMemory,void*,const uint8_t[512],const int32_t[12],void**,size_t*,void**,size_t*,unsigned*);
/* Callback results are explicit: missing inputs fail; original owned no-draw
   is accepted only by exact endpoint assembly (alpha==0). No-draw leaves
   rotation/palette outputs unused. Paired presentation must resolve its own
   visibility semantics and cannot reuse an endpoint no-draw result. */
typedef enum {NF_MODEL_INPUT_MISSING=0,NF_MODEL_INPUT_READY=1,NF_MODEL_INPUT_OWNED_NO_DRAW=2} NFSceneModelInputResult;
typedef int (*NFSceneModelInputs)(void*,unsigned,const NFNativeSceneCommand*,const uint32_t[5],int32_t[12],uint8_t[512]);
typedef int (*NFScenePalette)(void*,unsigned,const NFNativeSceneCommand*,NFReadMemory,void*,const int32_t[12],uint8_t[512]);
/* Successful resolver transfers owned surface/lighting. Assembly releases
   both allocations after copying, including on later scene rejection. */
typedef int (*NFScenePaletteAssets)(void*,unsigned,const NFNativeSceneCommand*,NFReadMemory,void*,const int32_t[12],uint8_t[512],void**,size_t*,void**,size_t*);
/* Resolve exact world kind/source/material palettes; reject visibly different candidates. Output unchanged on failure. */
/* Reader must expose stable scene-owned bytes for the duration of validation.
   Identical sealed palette bytes reuse the first validated command asset. */
__declspec(dllexport) int nf_scene_command_palette(const NFDrawPalettes*,uint64_t,uint32_t,const NFNativeSceneCommand*,NFReadMemory,void*,const int32_t[12],uint8_t[512]);
/* Same validation, transferring the already extracted owned surface/lighting.
   All outputs remain unchanged on failure. Free assets with nf_surface_free. */
__declspec(dllexport) int nf_scene_command_palette_extract(const NFDrawPalettes*,uint64_t,uint32_t,const NFNativeSceneCommand*,NFReadMemory,void*,const int32_t[12],uint8_t[512],void**,size_t*,void**,size_t*);
__declspec(dllexport) void nf_scene_command_palette_detail(uint32_t[4]);
/* Cumulative diagnostic counts: calls, matched entries, duplicates avoided,
   exact-key extractions, consensus calls, consensus extractions. */
__declspec(dllexport) void nf_scene_command_palette_stats(uint64_t[6]);
/* A newly visible source may lack an exact key. Accept only if all captured
   world palettes across both scenes give identical visible asset/light colors. */
__declspec(dllexport) int nf_scene_command_palette_consensus(const NFDrawPalettes*,uint32_t,const NFDrawPalettes*,uint32_t,uint64_t,const NFNativeSceneCommand*,NFReadMemory,void*,const int32_t[12],uint8_t[512]);
__declspec(dllexport) int nf_scene_command_palette_consensus_extract(const NFDrawPalettes*,uint32_t,const NFDrawPalettes*,uint32_t,uint64_t,const NFNativeSceneCommand*,NFReadMemory,void*,const int32_t[12],uint8_t[512],void**,size_t*,void**,size_t*);
/* Owned road texels: first material-width bytes of each double-width row.
   Rejects shift0/non-power-of-two stored heights: their mask domain
   cannot be represented by this periodic texture layout. */
__declspec(dllexport) int nf_road_texture_indices_layer_owned(NFReadMemory,void*,uint32_t,uint32_t,unsigned,uint8_t**,uint32_t*,uint32_t*);
__declspec(dllexport) int nf_road_texture_indices_owned(NFReadMemory,void*,uint32_t,uint32_t,uint8_t**,uint32_t*,uint32_t*);
#endif
