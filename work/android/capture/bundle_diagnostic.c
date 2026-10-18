#include "nfsug_capture.h"
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"bundle diagnostic line %d\n",__LINE__);return 1;}}while(0)
static uint32_t table[256];
static uint32_t crc(const void*data,size_t n){const unsigned char*p=data;uint32_t c=~0u;while(n--)c=table[(c^*p++)&255]^(c>>8);return ~c;}
static uint64_t hash(const void*data,size_t n){const unsigned char*p=data;uint64_t h=14695981039346656037ull;while(n--){h^=*p++;h*=1099511628211ull;}return h;}
static FILE*output(const char*dir,const char*name){char path[1024];if(snprintf(path,sizeof(path),"%s/%s",dir,name)>=(int)sizeof(path))return NULL;return fopen(path,"wb");}
static uint64_t word(const void*p,unsigned i){uint64_t v;memcpy(&v,(const unsigned char*)p+i*8,8);return v;}
static uint32_t dword(const void*p,unsigned i){uint32_t v;memcpy(&v,(const unsigned char*)p+i*4,4);return v;}
int main(int argc,char**argv){
 CHECK(argc==4);for(unsigned i=0;i<256;i++){uint32_t c=i;for(unsigned j=0;j<8;j++)c=(c>>1)^((c&1)?0xedb88320u:0);table[i]=c;}
 CHECK(crc("123456789",9)==0xcbf43926u&&hash("abc",3)==0xe71fa2190541574bull);
 FILE*f=fopen(argv[2],"rb");CHECK(f);fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);CHECK(size>0&&size<1048576);void*state=malloc(size);CHECK(state&&fread(state,1,size,f)==(size_t)size);fclose(f);
 NFAAndroidCore*c=nfa_core_open(argv[1]);CHECK(c&&nfa_core_load_state(c,state,size)&&nfa_core_capture_enable(c,1)&&nfa_core_capture_layers(c,1));
 FILE*frames=output(argv[3],"frames.raw"),*audio=output(argv[3],"audio.raw"),*digests=output(argv[3],"bundles.bin");CHECK(frames&&audio&&digests);
 uint64_t initial[4],now[4],info[5],last_epoch=0,last_refresh=0;CHECK(nfa_core_timing(c,initial));unsigned counts[3]={0},row_checks=0,missing=0;int16_t pcm[8192];unsigned char*retained[3]={0};size_t retained_size[3]={0};uint64_t retained_hash[3]={0};
 for(unsigned frame=0;frame<600;frame++){
  unsigned keys=1|(frame>=60&&frame<120?16:frame>=480&&frame<540?32:0);CHECK(nfa_core_step(c,keys)==1&&nfa_core_timing(c,now)&&now[0]==16777216&&now[1]==280896&&now[2]==initial[2]+frame+1&&now[3]==frame+1);
  CHECK(fwrite(nfa_core_pixels(c),1,153600,frames)==153600);size_t n=nfa_core_read_audio(c,pcm,4096);CHECK(n<=4096&&fwrite(pcm,4,n,audio)==n);
  CHECK(nfa_core_capture_layer_info(c,info));n=nfa_core_capture_bundle(c,info[0],(unsigned)info[1],NULL,0);uint64_t record[6]={frame+1,n,0,0,0,0};
  if(!n){CHECK(frame<6);missing++;CHECK(fwrite(record,sizeof(record),1,digests)==1);continue;}
  CHECK(n<64*1024*1024);unsigned char*data=malloc(n);CHECK(data);memset(data,165,n);CHECK(!nfa_core_capture_bundle(c,info[0],(unsigned)info[1],data,n-1));for(size_t j=0;j<n;j++)CHECK(data[j]==165);
  CHECK(nfa_core_capture_bundle(c,info[0],(unsigned)info[1],data,n)==n&&word(data,0)==0x3142414e&&word(data,1)==1&&word(data,2)==n&&word(data,3)==info[0]&&word(data,4)==info[1]);
  unsigned kind=(unsigned)word(data,5),count=(unsigned)word(data,7);CHECK((kind==1&&count==1&&!word(data,6))||(kind==2&&count==2&&word(data,6)>0&&word(data,6)<160));
  size_t offset=128;for(unsigned j=0;j<4;j++){CHECK(word(data,8+j*2)==offset&&word(data,9+j*2)<=n-offset);offset+=word(data,9+j*2);}CHECK(offset==n);
  for(unsigned j=0;j<count;j++){size_t bytes=word(data,9+j*2);unsigned char*packet=data+word(data,8+j*2);unsigned serial=dword(packet,4);CHECK(nfa_core_capture_owned_packet(c,info[0],serial,NULL,0)==bytes);void*copy=malloc(bytes);CHECK(copy&&nfa_core_capture_owned_packet(c,info[0],serial,copy,bytes)==bytes&&!memcmp(copy,packet,bytes));free(copy);}
  uint64_t provenance[664];CHECK(word(data,15)==sizeof(provenance)&&nfa_core_capture_provenance(c,info[0],(unsigned)info[1],provenance,sizeof(provenance))==sizeof(provenance)&&!memcmp(provenance,data+word(data,14),sizeof(provenance)));
  unsigned char*layer=data+word(data,12);size_t layer_size=word(data,13);unsigned pages=dword(layer,4);CHECK(dword(layer,0)==0x31504c4e&&dword(layer,1)==1&&dword(layer,2)==layer_size&&dword(layer,3)==160&&pages>0&&pages<=4000&&dword(layer,5)==25&&dword(layer,6)==4096&&dword(layer,7)==info[1]&&layer_size==28512+(size_t)pages*4096);
  for(unsigned y=0;y<160;y++)for(unsigned j=0;j<25;j++){uint16_t ref;memcpy(&ref,layer+20512+(y*25+j)*2,2);CHECK(ref<pages);}
  for(unsigned y=0;y<160;y++)if(!counts[kind]||y==0||y==79||y==159){unsigned char direct[100480],decoded[100480];CHECK(nfa_core_capture_layer_row(c,info[0],(unsigned)info[1],y,direct,sizeof(direct))==sizeof(direct));memcpy(decoded,layer+32+y*128,128);for(unsigned j=0;j<25;j++){uint16_t ref;memcpy(&ref,layer+20512+(y*25+j)*2,2);memcpy(decoded+128+j*4096,layer+28512+(size_t)ref*4096,j==24?2048:4096);}CHECK(!memcmp(direct,decoded,sizeof(direct)));row_checks++;}
  record[2]=crc(data,n);record[3]=hash(data,n);record[4]=kind;record[5]=word(data,6);CHECK(fwrite(record,sizeof(record),1,digests)==1);
  if(!counts[kind]){retained[kind]=malloc(n);CHECK(retained[kind]);memcpy(retained[kind],data,n);retained_size[kind]=n;retained_hash[kind]=record[3];FILE*sample=output(argv[3],kind==1?"whole.nab":"split.nab");CHECK(sample&&fwrite(data,1,n,sample)==n&&!fclose(sample));}
  counts[kind]++;last_epoch=info[0];last_refresh=info[1];free(data);
 }
 CHECK(counts[1]==481&&counts[2]==113&&missing==6&&row_checks==2096&&!fclose(frames)&&!fclose(audio)&&!fclose(digests));
 CHECK(nfa_core_load_state(c,state,size)&&!nfa_core_capture_bundle(c,last_epoch,(unsigned)last_refresh,NULL,0));CHECK(nfa_core_capture_layers(c,0)&&!nfa_core_capture_bundle(c,last_epoch,(unsigned)last_refresh,NULL,0));nfa_core_close(c);
 for(unsigned i=1;i<3;i++){CHECK(retained[i]&&hash(retained[i],retained_size[i])==retained_hash[i]);free(retained[i]);}free(state);
 puts("PASS_ANDROID_OWNED_BUNDLE_594_ROWS_2096");return 0;
}
