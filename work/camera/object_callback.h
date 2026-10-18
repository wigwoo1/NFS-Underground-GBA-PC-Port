#ifndef NF_OBJECT_CALLBACK_H
#define NF_OBJECT_CALLBACK_H
#include "object_ground.h"
/* Adapter must operate on staged object/owned scratch only, never live game. */
typedef int (*NFObjectProjection)(void*,const uint8_t[256],uint8_t[164]);
__declspec(dllexport) int nf_object_damage(uint8_t[164],unsigned*);
/* Selector12 core; sound10 returned as event. Requires isolated projection
   adapter. Object/event atomic; adapter-owned scratch needs its own staging. */
__declspec(dllexport) int nf_object_callback12(const uint8_t[256],uint8_t[164],NFVisibilityRead,void*,NFObjectProjection,void*,unsigned*);
#endif
