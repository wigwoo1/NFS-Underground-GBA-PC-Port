#ifndef NF_SCENE_PACKET_H
#define NF_SCENE_PACKET_H
#include <stdint.h>
#include <stddef.h>
#include "snapshot_store.h"
#include "road_source_attributes.h"
typedef struct {const uint8_t*data;size_t size;} NFSceneSection;
typedef struct {uint32_t serial,begin_refresh,end_refresh,page;NFSceneSection section[5];} NFScenePacket;
/* Optional NFM2 NZI1 trailer: magic,width,height,reserved=0, then width*height
   original texel indices. Index0 overwrites framebuffer data but has no mode4 BG2 display coverage.
   Attach copies model+indices; borrow accessor is atomic on absence/failure.
   Renderers must explicitly consume this metadata or reject the asset. */
__declspec(dllexport) int nf_scene_model_attach_indices(NFSceneSection,const uint8_t*,size_t,void**,size_t*);
__declspec(dllexport) int nf_scene_model_indices(NFSceneSection,const uint8_t**,size_t*);
/* Optional world NWI1 trailer preserves original indices per surface.
   Attach adds or replaces one opaque-span surface while preserving all
   previously attached surfaces in an owned copy.
   Borrow validates the entire trailer atomically. Consumers must reject
   unsupported indexed world records rather than silently flatten them. */
__declspec(dllexport) int nf_scene_world_attach_indices(NFSceneSection,unsigned,const uint8_t*,size_t,void**,size_t*);
__declspec(dllexport) int nf_scene_world_indices(NFSceneSection,unsigned,const uint8_t**,size_t*);
/* NWI1 mode4 is affine road mapping; mode1 is perspective. Legacy indices
   accessor intentionally rejects mode4 to prevent silently losing its mode. */
__declspec(dllexport) int nf_scene_world_attach_road_mapping(NFSceneSection,unsigned,const uint8_t*,size_t,unsigned,void**,size_t*);
__declspec(dllexport) int nf_scene_world_road_mapping(NFSceneSection,unsigned,const uint8_t**,size_t*,unsigned*);
/* Modes5/6: perspective/affine indices followed by owned288byte raw source
   attributes. Mapping borrow returns indices only; attribute borrow copies.
   Legacy indices accessor rejects these modes. Outputs atomic on failure. */
__declspec(dllexport) int nf_scene_road_attributes_match(NFSceneSection,const NFRoadSourceAttributes*);
__declspec(dllexport) int nf_scene_world_attach_road_attributes(NFSceneSection,unsigned,const uint8_t*,size_t,const NFRoadSourceAttributes*,void**,size_t*);
__declspec(dllexport) int nf_scene_world_road_attributes(NFSceneSection,unsigned,NFRoadSourceAttributes*);
__declspec(dllexport) int nf_scene_world_wall_states(NFSceneSection,unsigned,const uint8_t**,size_t*,unsigned*);
__declspec(dllexport) int nf_scene_world_attach_wall_states(NFSceneSection,unsigned,const uint8_t*,size_t,unsigned,void**,size_t*);
/* Modes7/8: base or17 planes, classifications followed by output indices.
   Both arrays have identical size. Skip and write0 remain distinct. */
__declspec(dllexport) int nf_scene_world_attach_wall_indices(NFSceneSection,unsigned,const uint8_t*,const uint8_t*,size_t,unsigned,void**,size_t*);
__declspec(dllexport) int nf_scene_world_wall_indices(NFSceneSection,unsigned,const uint8_t**,const uint8_t**,size_t*,unsigned*);
/* NSP1: 8 little-endian words, then five tag/offset/size directory entries.
   Tags 1..5: NFM2 current-pose model, RFD1 world, NFO1 order, NFL1 lighting,
   NFI1 identities (kind/state/source/base/reserved per entry). No pointers on disk.
   Views borrow storage and must not outlive their acquired snapshot pair. */
__declspec(dllexport) int nf_scene_packet_view(const void*,size_t,NFScenePacket*);
/* NSP2 model section: NML1/count, ordered offset/size directory, 2..16 NFM2s.
   Model command j is UINT32_MAX-j; identity rows follow world surfaces.
   NSP1 remains byte-compatible for one model. Accessors borrow packet storage. */
__declspec(dllexport) unsigned nf_scene_packet_model_count(const NFScenePacket*);
__declspec(dllexport) int nf_scene_packet_model(const NFScenePacket*,unsigned,NFSceneSection*);
/* Map each older model index to its unique identity-matched newer index.
   World counts may differ; output stays unchanged on failure. */
__declspec(dllexport) int nf_scene_packet_pair_model_indices(const NFScenePacket*,const NFScenePacket*,unsigned*,size_t);
/* Map older model membership by unique complete identity, allowing different
   counts. UINT32_MAX means missing/ambiguous. Never matches by screen position.
   Outputs stay unchanged on invalid input. Strict pairing above is unchanged. */
__declspec(dllexport) int nf_scene_packet_pair_model_subset(const NFScenePacket*,const NFScenePacket*,unsigned*,size_t,unsigned*);
/* Map older world surfaces by identity. UINT32_MAX marks missing or ambiguous
   identities; matched receives the count. Outputs stay unchanged on invalid input. */
__declspec(dllexport) int nf_scene_packet_pair_world_indices(const NFScenePacket*,const NFScenePacket*,unsigned*,size_t,unsigned*);
__declspec(dllexport) int nf_scene_packet_push(NFSnapshotStore*,uint64_t epoch,const void*,size_t);
/* Copy five prepared sections into a validated owned packet. Output arguments
   stay unchanged on failure. Release successful output with the matching API. */
__declspec(dllexport) int nf_scene_packet_build(const NFScenePacket*,void**data,size_t*size);
__declspec(dllexport) void nf_scene_packet_free(void*);
/* Optional candidate_packet.c: insert one unlit wall before command position.
   Caller binds asset/identity/anchor to scene. Same owned-output/free contract. */
__declspec(dllexport) int nf_scene_packet_insert_wall(const void*,size_t,const void*,size_t,const uint32_t[5],unsigned,void**,size_t*);
/* Optional candidate_packet.c: primary opaque road with kind1 identity.
   Same caller-proven scene/anchor and owned-output contract as wall insertion. */
__declspec(dllexport) int nf_scene_packet_insert_road(const void*,size_t,const void*,size_t,const uint32_t[5],unsigned,void**,size_t*);
/* Optional owned NFB1 identity-section trailer: sampled alpha and surface bounds. */
__declspec(dllexport) int nf_scene_packet_with_bounds(const void*,size_t,double,const uint16_t*,unsigned,void**,size_t*);
__declspec(dllexport) int nf_scene_packet_bounds(const NFScenePacket*,double*,const uint8_t**);
/* NFB2 retains world bounds followed by each model's source portal bounds. */
__declspec(dllexport) int nf_scene_packet_model_bounds(const NFScenePacket*,const uint8_t**);
/* Atomic borrow of one validated world surface core (vertices/UV/texture). */
__declspec(dllexport) int nf_scene_world_surface(NFSceneSection,unsigned,NFSceneSection*);
typedef struct {const uint8_t*data;size_t size;unsigned mode;} NFWorldMetadata;
/* Atomic bounded bulk borrow; validates all metadata once. */
__declspec(dllexport) int nf_scene_world_metadata_all(NFSceneSection,NFWorldMetadata*,unsigned,unsigned*);


/* Modes9/10: indices, versioned raw camera56, raw source attributes288. */
typedef struct {uint32_t version,address;int32_t matrix[12];} NFRoadCameraMetadata;
__declspec(dllexport) int nf_scene_world_attach_road_camera(NFSceneSection,unsigned,const uint8_t*,size_t,const NFRoadSourceAttributes*,const NFRoadCameraMetadata*,void**,size_t*);
__declspec(dllexport) int nf_scene_world_road_camera(NFSceneSection,unsigned,NFRoadCameraMetadata*);

#endif

