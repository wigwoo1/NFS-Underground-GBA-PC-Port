/* Opt-in timestamp pool; result retrieval only after every query is available. */
#define NF_GPU_QUERY_SLOTS 16
static GLuint probe_queries[64];static uint64_t probe_ids[16];static unsigned probe_head,probe_count,probe_mode,probe_error;static int probe_active=-1;
static uint64_t probe_sequence,probe_skipped,probe_completed;
static void(APIENTRY*probe_gen)(GLsizei,GLuint*);static void(APIENTRY*probe_delete)(GLsizei,const GLuint*);static void(APIENTRY*probe_stamp)(GLuint,GLenum);
static void(APIENTRY*probe_available)(GLuint,GLenum,GLint*);static void(APIENTRY*probe_result)(GLuint,GLenum,uint64_t*);
static void probe_clear(void){if(probe_queries[0]&&probe_delete){probe_delete(64,probe_queries);}memset(probe_queries,0,sizeof(probe_queries));probe_head=probe_count=probe_mode=probe_error=0;probe_active=-1;probe_sequence=probe_skipped=probe_completed=0;}
__declspec(dllexport) unsigned nf_owned_gpu_query_pending(void){return probe_count;}
__declspec(dllexport) int nf_owned_gpu_query_mode(unsigned enabled){
 if(gpu_owner!=GetCurrentThreadId()||enabled>1)return 31;
 if(enabled==probe_mode)return 0;
 if(!enabled){probe_clear();return 0;}
 probe_gen=(void*)wglGetProcAddress("glGenQueries");probe_delete=(void*)wglGetProcAddress("glDeleteQueries");probe_stamp=(void*)wglGetProcAddress("glQueryCounter");probe_available=(void*)wglGetProcAddress("glGetQueryObjectiv");probe_result=(void*)wglGetProcAddress("glGetQueryObjectui64v");
 if((uintptr_t)probe_gen<=3||(intptr_t)probe_gen==-1||(uintptr_t)probe_delete<=3||(intptr_t)probe_delete==-1||(uintptr_t)probe_stamp<=3||(intptr_t)probe_stamp==-1||(uintptr_t)probe_available<=3||(intptr_t)probe_available==-1||(uintptr_t)probe_result<=3||(intptr_t)probe_result==-1)return 39;
 probe_gen(64,probe_queries);if(glGetError()){probe_clear();return 8;}probe_mode=1;return 0;
}
static void probe_draw_begin(void){
 if(!probe_mode)return;
 /* Pause may cancel a draw before presentation: discard only its unfinished diagnostic slot. */
 probe_sequence++;if(probe_active!=-1){probe_count--;probe_active=-1;probe_skipped++;}
 if(probe_count==16){probe_skipped++;return;}
 probe_active=(int)((probe_head+probe_count)%16);probe_ids[probe_active]=probe_sequence;probe_count++;probe_stamp(probe_queries[probe_active*4],0x8e28);
}
static void probe_marker(unsigned marker){if(probe_mode&&probe_active>=0){probe_stamp(probe_queries[probe_active*4+marker],0x8e28);if(marker==3)probe_active=-1;}}
__declspec(dllexport) int nf_owned_gpu_query_read(uint64_t*out){
 if(!out||gpu_owner!=GetCurrentThreadId())return 31;
 memset(out,0,104*sizeof(*out));out[0]=probe_mode;out[3]=probe_skipped;out[4]=probe_sequence;out[7]=probe_sequence;
 if(probe_mode){while(probe_count&&out[2]<16){
  if((int)probe_head==probe_active)break;
  int ready=1;for(unsigned i=0;i<4;i++){GLint available=0;probe_available(probe_queries[probe_head*4+i],0x8867,&available);if(!available){ready=0;break;}}
  if(!ready)break;
  uint64_t*record=out+8+out[2]*6;record[0]=probe_ids[probe_head];for(unsigned i=0;i<4;i++){probe_result(probe_queries[probe_head*4+i],0x8866,&record[i+1]);}
  LARGE_INTEGER a,b;QueryPerformanceCounter(&a);QueryPerformanceFrequency(&b);record[5]=(uint64_t)(a.QuadPart*1000000000.0/b.QuadPart);
  if(record[1]>record[2]||record[2]>record[3]||record[3]>record[4])probe_error=2;
  out[2]++;probe_completed++;probe_head=(probe_head+1)%16;probe_count--;
 }}out[1]=probe_count;out[5]=probe_completed;out[6]=probe_error;return probe_error?37:0;
}
