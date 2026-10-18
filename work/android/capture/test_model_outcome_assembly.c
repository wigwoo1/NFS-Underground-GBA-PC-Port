#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "scene_assembly.h"
static unsigned calls,reads;static int selected_result;
static int read_memory(void*u,uint32_t a,void*p,size_t n){(void)u;(void)a;(void)p;(void)n;reads++;return 0;}
static int palette(void*u,unsigned i,const NFNativeSceneCommand*c,NFReadMemory r,void*x,const int32_t rotation[12],uint8_t colors[512]){(void)u;(void)i;(void)c;(void)r;(void)x;(void)rotation;(void)colors;assert(0);return 0;}
static int model(void*u,unsigned i,const NFNativeSceneCommand*c,const uint32_t id[5],int32_t rotation[12],uint8_t colors[512]){(void)u;(void)i;(void)rotation;(void)colors;assert(c->kind==5&&id[0]==3&&id[2]==c->source);calls++;return selected_result;}
int main(void){
 NFNativeSceneCommand commands[2];memset(commands,0,sizeof(commands));commands[0].kind=commands[1].kind=5;commands[0].source=1;commands[1].source=2;
 uint32_t ids[10]={3,4,1,5,0,3,4,2,5,0};int32_t rotation[12]={0};static uint32_t table[32768];void*out=NULL;size_t bytes=0;
 selected_result=NF_MODEL_INPUT_OWNED_NO_DRAW;calls=reads=0;
 assert(!nf_assembly_commands_model_inputs(commands,2,ids,NULL,0.0,read_memory,NULL,palette,NULL,rotation,model,NULL,1,100,104,0,table,&out,&bytes));assert(calls==2&&reads==0);
 calls=reads=0;assert(!nf_assembly_commands_model_inputs(commands,2,ids,NULL,0.5,read_memory,NULL,palette,NULL,rotation,model,NULL,1,100,104,0,table,&out,&bytes));assert(calls==1&&reads==0);
 selected_result=NF_MODEL_INPUT_MISSING;calls=reads=0;assert(!nf_assembly_commands_model_inputs(commands,2,ids,NULL,0.0,read_memory,NULL,palette,NULL,rotation,model,NULL,1,100,104,0,table,&out,&bytes));assert(calls==1&&reads==0);
 selected_result=99;calls=reads=0;assert(!nf_assembly_commands_model_inputs(commands,2,ids,NULL,0.0,read_memory,NULL,palette,NULL,rotation,model,NULL,1,100,104,0,table,&out,&bytes));assert(calls==1&&reads==0);
 puts("PASS_ASSEMBLY_OWNED_NO_DRAW_ENDPOINT_ONLY_MISSING_AND_INVALID_REJECT");return 0;
}
