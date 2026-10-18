#ifndef NF_OBJECT_PROJECTION_H
#define NF_OBJECT_PROJECTION_H
#include "native_visibility.h"
typedef int (*NFObjectMatrixBuilder)(void*,const uint32_t[12],const uint8_t[164],uint32_t[12]);
/* Original80239C0 slot/flag allocation. Matrix builder uses staged48bytes;
   fails atomically when active matrix behavior is unavailable. */
__declspec(dllexport) int nf_object_projection_slot(const uint8_t[256],uint8_t[164],uint32_t*,uint8_t[64*48],NFVisibilityRead,void*,NFObjectMatrixBuilder,void*);
/* Original8022C24: fixed-point matrix construction, isolated asset reader. */
__declspec(dllexport) int nf_object_projection_matrix(const uint32_t[12],const uint8_t[164],uint32_t[12],NFVisibilityRead,void*);
/* Whole selector12 with native projection and staged owned scratch/counter. */
__declspec(dllexport) int nf_object_callback12_owned(const uint8_t[256],uint8_t[164],uint32_t*,uint8_t[64*48],NFVisibilityRead,void*,unsigned*);
#endif
