#ifndef NF_ROAD_NEAR_ATTRIBUTES_H
#define NF_ROAD_NEAR_ATTRIBUTES_H
#include <stdint.h>
__declspec(dllexport) int nf_road_vertex_attributes(double,const int32_t[2],unsigned,unsigned,unsigned,const uint32_t*,double[2]);
__declspec(dllexport) int nf_road_near_attributes(double,double,const int32_t[4],unsigned,unsigned,unsigned,int,const uint32_t*,double[2]);
#endif
