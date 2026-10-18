/* Optional complete-frame GPU timestamp pairs. Never wait for results in live loop. */
typedef struct {GLuint ids[2];uint64_t epoch;double target;unsigned kind,active;} NFGpuTimerSlot;
typedef struct {NFGpuTimerSlot slots[64];FILE*file;unsigned enabled,pending,started,resolved;void(APIENTRY*gen)(GLsizei,GLuint*);void(APIENTRY*remove)(GLsizei,const GLuint*);void(APIENTRY*stamp)(GLuint,GLenum);void(APIENTRY*available)(GLuint,GLenum,GLint*);void(APIENTRY*value)(GLuint,GLenum,uint64_t*);} NFGpuTimer;
static int nf_gpu_proc_valid(PROC p){return p&&p!=(PROC)1&&p!=(PROC)2&&p!=(PROC)3&&p!=(PROC)(intptr_t)-1;}
static int nf_gpu_timer_open(NFGpuTimer*t,const char*prefix){
 memset(t,0,sizeof(*t));if(!getenv("NF_TEST_GPU_TIMESTAMPS"))return 1;
 t->gen=(void*)wglGetProcAddress("glGenQueries");t->remove=(void*)wglGetProcAddress("glDeleteQueries");t->stamp=(void*)wglGetProcAddress("glQueryCounter");t->available=(void*)wglGetProcAddress("glGetQueryObjectiv");t->value=(void*)wglGetProcAddress("glGetQueryObjectui64v");
 if(!nf_gpu_proc_valid((PROC)t->gen)||!nf_gpu_proc_valid((PROC)t->remove)||!nf_gpu_proc_valid((PROC)t->stamp)||!nf_gpu_proc_valid((PROC)t->available)||!nf_gpu_proc_valid((PROC)t->value))return 0;
 char path[1500];snprintf(path,sizeof(path),"%s-gpu.csv",prefix);t->file=fopen(path,"wb");if(!t->file)return 0;t->enabled=1;
 fprintf(t->file,"epoch,target,kind,gpu_begin_ns,gpu_end_ns,gpu_elapsed_ns\n");
 for(unsigned i=0;i<64;i++){t->gen(2,t->slots[i].ids);if(!t->slots[i].ids[0]||!t->slots[i].ids[1])return 0;}return glGetError()==GL_NO_ERROR;
}
static int nf_gpu_timer_poll(NFGpuTimer*t){
 if(!t->enabled)return 1;
 for(unsigned i=0;i<64;i++){NFGpuTimerSlot*s=t->slots+i;if(!s->active)continue;GLint ready=0;t->available(s->ids[1],0x8867,&ready);if(!ready)continue;
 uint64_t begin=0,end=0;t->value(s->ids[0],0x8866,&begin);t->value(s->ids[1],0x8866,&end);if(end<begin||!begin)return 0;
 if(fprintf(t->file,"%llu,%.12f,%u,%llu,%llu,%llu\n",(unsigned long long)s->epoch,s->target,s->kind,(unsigned long long)begin,(unsigned long long)end,(unsigned long long)(end-begin))<0)return 0;
 s->active=0;t->pending--;t->resolved++;}return glGetError()==GL_NO_ERROR;
}
static int nf_gpu_timer_begin(NFGpuTimer*t,uint64_t epoch,double target,unsigned kind){
 if(!t->enabled)return -1;if(!nf_gpu_timer_poll(t))return -2;
 for(unsigned i=0;i<64;i++){NFGpuTimerSlot*s=t->slots+i;if(!s->active){s->epoch=epoch;s->target=target;s->kind=kind;s->active=1;t->pending++;t->started++;t->stamp(s->ids[0],0x8e28);return (int)i;}}return -2;
}
static int nf_gpu_timer_end(NFGpuTimer*t,int slot){if(slot==-1)return 1;if(slot<0)return 0;t->stamp(t->slots[slot].ids[1],0x8e28);return glGetError()==GL_NO_ERROR;}
static int nf_gpu_timer_close(NFGpuTimer*t){
 if(!t->enabled)return 1;glFinish();int ok=nf_gpu_timer_poll(t)&&!t->pending&&t->started==t->resolved;
 printf("gpu_timer_started=%u gpu_timer_resolved=%u gpu_timer_pending=%u\n",t->started,t->resolved,t->pending);
 if(t->remove)for(unsigned i=0;i<64;i++)t->remove(2,t->slots[i].ids);if(t->file&&fclose(t->file))ok=0;return ok;
}
