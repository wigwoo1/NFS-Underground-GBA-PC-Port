#ifndef NF_PC_SCENE_SAMPLE_INTERNAL_H
#define NF_PC_SCENE_SAMPLE_INTERNAL_H
#include "scene_sample.h"
#include "scene_internal.h"
typedef struct {NFPCSceneCommand command;uint64_t trace[5];NFPCModelMesh*model;NFPCWorldMesh*world;float*planes;} NFPCSceneSampleDraw;
struct NFPCSceneSample {NFPCScene*base;uint64_t info[16],bands[3][12];double target,fractions[3][2];unsigned char background[153600];NFPCSceneSampleDraw draws[864];};
#endif
