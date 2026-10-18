#ifndef NF_SCENE_H
#define NF_SCENE_H
#include <stdint.h>
#define NF_MAX_VERTS 32
#define NF_MAX_POLYS 4096
typedef struct {float x,y,s,t,q;} NFVertex;
typedef struct {uint32_t address,width,height,stride;uint32_t count,kind,shade; NFVertex v[NF_MAX_VERTS];} NFPoly;
void nf_scene_enable(int);
const NFPoly* nf_scene(int* count);
void nf_overlay(uint32_t* out);
int nf_texture(const NFPoly*,uint32_t* out);
void nf_scene_reset(void);
#endif
