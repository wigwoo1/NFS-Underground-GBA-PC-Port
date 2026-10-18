#include "nfsug_capture.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"layer diagnostic failed line %d\n",__LINE__);return 1;}}while(0)
int main(int argc,char**argv){
 CHECK(argc==4);FILE*f=fopen(argv[2],"rb");CHECK(f);fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);CHECK(n>0&&n<1048576);
 void*state=malloc(n);CHECK(state&&fread(state,1,n,f)==(size_t)n);fclose(f);
 NFAAndroidCore*c=nfa_core_open(argv[1]);CHECK(c&&nfa_core_load_state(c,state,n)&&nfa_core_capture_enable(c,1)&&nfa_core_capture_layers(c,1));
 char path[1024];CHECK(snprintf(path,sizeof(path),"%s/rows.bin",argv[3])<(int)sizeof(path));FILE*rows=fopen(path,"wb");CHECK(rows);
 CHECK(snprintf(path,sizeof(path),"%s/frames.raw",argv[3])<(int)sizeof(path));FILE*frames=fopen(path,"wb");CHECK(frames);
 uint64_t info[5],old[5],timing[4];unsigned ys[3]={0,79,159};size_t size=100480;unsigned char*row=malloc(size);CHECK(row);
 for(unsigned pass=0;pass<2;pass++){
  if(pass){memcpy(old,info,sizeof(old));CHECK(nfa_core_load_state(c,state,n));memset(row,165,size);
   CHECK(!nfa_core_capture_layer_info(c,info)&&!nfa_core_capture_layer_row(c,old[0],old[1],0,row,size));
   for(size_t i=0;i<size;i++)CHECK(row[i]==165);
  }
  for(unsigned frame=0;frame<40;frame++){
   CHECK(nfa_core_step(c,1)==1&&nfa_core_timing(c,timing)&&timing[0]==16777216&&timing[1]==280896&&timing[3]==frame+1);
   CHECK(fwrite(nfa_core_pixels(c),1,153600,frames)==153600);
   CHECK(nfa_core_capture_layer_info(c,info)&&fwrite(info,sizeof(info),1,rows)==1);
   for(unsigned j=0;j<3;j++){
    CHECK(nfa_core_capture_layer_row(c,info[0],info[1],ys[j],NULL,0)==size);memset(row,165,size);
    CHECK(!nfa_core_capture_layer_row(c,info[0],info[1],ys[j],row,size-1));for(size_t i=0;i<size;i++)CHECK(row[i]==165);
    CHECK(nfa_core_capture_layer_row(c,info[0],info[1],ys[j],row,size)==size&&fwrite(row,1,size,rows)==size);
   }
  }
 }
 CHECK(nfa_core_pause(c,1));memcpy(old,info,sizeof(old));for(unsigned i=0;i<10;i++)CHECK(nfa_core_step(c,1)==2&&nfa_core_capture_layer_info(c,info)&&!memcmp(old,info,sizeof(old)));
 CHECK(nfa_core_pause(c,0)&&nfa_core_capture_layers(c,0)&&!nfa_core_capture_layer_info(c,info)&&!nfa_core_capture_layer_row(c,old[0],old[1],0,NULL,0));
 CHECK(!fclose(rows)&&!fclose(frames));nfa_core_close(c);free(row);free(state);
 puts("PASS_AUXILIARY_ROWS_80_FRAMES_240_COPIES");return 0;
}
