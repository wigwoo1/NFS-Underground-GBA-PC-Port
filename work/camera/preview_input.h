#include <string.h>
typedef struct {const uint8_t*data;size_t size;} PreviewMemory;
typedef struct {FILE*file;PreviewMemory memory;size_t position;} PreviewInput;
static PreviewMemory preview_memory[5];
static PreviewInput*preview_input(unsigned slot,const char*path){
 PreviewInput*in=calloc(1,sizeof(*in));if(!in)return NULL;
 if(preview_memory[slot].data)in->memory=preview_memory[slot];
 else{in->file=fopen(path,"rb");if(!in->file){free(in);return NULL;}}
 return in;
}
static int read_bytes(PreviewInput*in,void*out,size_t size){
 if(!in)return 0;
 if(in->file)return fread(out,1,size,in->file)==size;
 if(size>in->memory.size-in->position)return 0;
 memcpy(out,in->memory.data+in->position,size);in->position+=size;return 1;
}
static int preview_end(PreviewInput*in){return in->file?fgetc(in->file)==EOF:in->position==in->memory.size;}
static void preview_close(PreviewInput*in){if(in){if(in->file)fclose(in->file);free(in);}}
