#ifndef NF_SCENE_COMMAND_PLAN_H
#define NF_SCENE_COMMAND_PLAN_H
#include "region_executor.h"
/* Road1/wall2/model5/billboard6. Material for world leaves=resolved address,
   texture,shift,height. Road XYZ=orientation,affine,secondary; wall XYZ[0]=flags.
   Road projected clip vertices, native span-derived bounds/cell end and selected wall scratch are owned copies. Wall bounds inherit the native region record. */
typedef struct {uint32_t kind,owner,pass,mask,object,source,xyz[3],material[4];uint8_t record[16],state[256],model[68];uint32_t billboard[18],vertex_count;uint8_t edge[52];int32_t vertices[128*6];uint16_t bounds[4];uint32_t cell_end;} NFNativeSceneCommand;
/* Explicit isolated callback adapter; cannot reenter live simulation. Return0
   rejects scene. Missing adapter rejects any required callback. */
typedef int (*NFSceneObjectCallback)(void*,unsigned,unsigned,uint8_t*,unsigned,uint8_t[32],uint32_t[12],uint32_t*,uint32_t*);
/* Atomic command/count/pool/bitmap publication. One initial state/snapshot;
   native traversal, collection and leaf setup. Not raster/asset assembly. */
__declspec(dllexport) int nf_scene_command_plan(const uint8_t[256],const void*,unsigned,uint8_t*,unsigned,uint8_t[32],NFVisibilityRead,void*,const uint32_t[32768],NFSceneObjectCallback,void*,NFNativeSceneCommand*,unsigned,unsigned*);
__declspec(dllexport) void nf_scene_command_plan_detail(uint32_t[18]);
/* Diagnostic prefix, capped at2048 visits; does not constrain traversal. */
__declspec(dllexport) void nf_scene_command_plan_visits(uint32_t[1+2048*3]);
/* All reached object slots, independent of diagnostic prefix capacity. */
__declspec(dllexport) void nf_scene_command_plan_object_mask(uint8_t[32]);
__declspec(dllexport) void nf_scene_command_plan_road(uint32_t[12+128*6]);
#endif
