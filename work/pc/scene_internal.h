#ifndef NF_PC_SCENE_INTERNAL_H
#define NF_PC_SCENE_INTERNAL_H
#include "source_scene.h"
#include "model_mesh.h"
#include "world_material.h"
#include "source_retention.h"
#include "source_hud.h"
typedef struct{uint64_t info[16];uint32_t source_identity[5];NFPCModelMesh*model;NFPCWorldMesh*world;NFPCWorldMaterial*material;const void*vertices;size_t vertices_bytes;float*planes;const void*image;unsigned char*owned_image;} NFPCSceneCommand;
struct NFPCScene{uint64_t info[8],owner[2][5];NFPCWorld*motion_source[2];unsigned char*motion_sky[2],*motion_timing[2];unsigned char background[153600],palette[163840];NFPCHud*hud;NFPCRetention*retained[2][2];float*retention_vertices[2][2];size_t retention_vertex_bytes[2][2];NFPCSceneCommand commands[288];};
#endif
