#ifndef NF_OBJECT_GROUND_H
#define NF_OBJECT_GROUND_H
#include "native_visibility.h"
/* Original8021F08: owned world-plane height, Q8 output, no simulation writes. */
__declspec(dllexport) int nf_object_ground_height(const uint8_t[256],unsigned,int32_t,int32_t,NFVisibilityRead,void*,int32_t*);
#endif
