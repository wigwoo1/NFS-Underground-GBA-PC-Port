#ifndef NF_ROAD_SOURCE_ATTRIBUTES_H
#define NF_ROAD_SOURCE_ATTRIBUTES_H
#include <stdint.h>
typedef struct {uint32_t count,shift,stored_height,affine,material,animation;int32_t offsets[2],attributes[32][2];} NFRoadSourceAttributes;
typedef char NFRoadSourceAttributesSize[(sizeof(NFRoadSourceAttributes)==288)?1:-1];
#endif
