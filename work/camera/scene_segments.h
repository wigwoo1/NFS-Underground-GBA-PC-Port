#ifndef NF_SCENE_SEGMENTS_H
#define NF_SCENE_SEGMENTS_H
#include <stdint.h>
#include "ordered_dispatch.h"
/* kind:1 wall,2 road,3 deferred,4 child,5 model. Child is UINT32_MAX otherwise.
   All slots remain original command positions. Caller binds one captured scene. */
typedef struct {uint32_t kind,begin,end,child;} NFSceneSegment;
typedef struct {uint32_t calls,count,parents[256],offsets[257];NFSceneSegment segments[1024];} NFSceneSegments;
__declspec(dllexport) int nf_scene_segments(const uint32_t*,unsigned,const uint32_t*,unsigned,const uint32_t*,const uint32_t*,NFSceneSegments*);
/* Revalidates captured segmentation. Only a nonempty direct wall segment may
   be extended. Rejects candidate sources already belonging to other commands.
   Caller must prove new sources belong to this region/phase and are eligible. */
__declspec(dllexport) int nf_segment_wall_insertions(const uint32_t*,unsigned,
 const uint32_t*,unsigned,const uint32_t*,const uint32_t*,unsigned,
 const uint32_t*,unsigned,NFWallInsertions*);
#endif

