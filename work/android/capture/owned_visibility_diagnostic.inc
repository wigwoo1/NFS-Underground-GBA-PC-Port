/* Isolated capture rejection evidence. No game or renderer decisions changed. */
#include <stdint.h>
#include <string.h>
static struct {uint64_t epoch;uint32_t words[12];} owned_visibility_rejections[256];
static void nf_owned_visibility_reject(uint64_t epoch,uint32_t serial,uint32_t reason,uint32_t pc,uint32_t frame,uint32_t state,uint32_t prepared,uint32_t stage,uint32_t query,uint32_t mismatch,uint32_t first,uint32_t bytes){
 unsigned slot=serial%256;uint32_t count=owned_visibility_rejections[slot].epoch==epoch&&owned_visibility_rejections[slot].words[0]==serial?owned_visibility_rejections[slot].words[11]:0;
 uint32_t row[12]={serial,reason,pc,frame,state,prepared,stage,query,mismatch,first,bytes,count+1};owned_visibility_rejections[slot].epoch=epoch;memcpy(owned_visibility_rejections[slot].words,row,sizeof(row));
}
__declspec(dllexport) int nf_owned_visibility_rejection(uint64_t epoch,uint32_t serial,uint32_t out[12]){
 unsigned slot=serial%256;if(!out||owned_visibility_rejections[slot].epoch!=epoch||owned_visibility_rejections[slot].words[0]!=serial||!owned_visibility_rejections[slot].words[11])return 0;memcpy(out,owned_visibility_rejections[slot].words,48);return 1;
}

#include <stdio.h>
#include <stdlib.h>
static void nf_owned_visibility_fixture(unsigned serial,uint32_t state,uint32_t selected,uint32_t recovery,const uint32_t base[2],const uint32_t query[12],const uint32_t view[12],const void*ram,size_t ram_bytes,const void*original,size_t original_bytes){
 const char*directory=getenv("NF_TEST_VISIBILITY_REJECTION_DIR");if(!directory||serial<17||serial>19)return;char path[1024];uint32_t header[4]={0x3146514e,state,selected,recovery};
 if(snprintf(path,sizeof(path),"%s/query-%u.nqf",directory,serial)<(int)sizeof(path)){FILE*f=fopen(path,"wb");if(f){fwrite(header,1,16,f);fwrite(base,1,8,f);fwrite(query,1,48,f);fwrite(view,1,48,f);fwrite(ram,1,ram_bytes,f);fclose(f);}}
 if(snprintf(path,sizeof(path),"%s/original-%u.bin",directory,serial)<(int)sizeof(path)){FILE*f=fopen(path,"wb");if(f){fwrite(original,1,original_bytes,f);fclose(f);}}
}
