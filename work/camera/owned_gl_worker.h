/* Persistent diagnostic; event acknowledgments serialize GL/global access.
   Producer-created window and synchronous scheduling remain unchanged. */
#include "submission_handoff.h"
typedef struct {NFSubmissionHandoff*queue;HANDLE thread,wake,done,stop;char**args;uint8_t*pixels;int result;DWORD producer,consumer;unsigned draws,starts,joins;} NFOwnedGLWorker;
static NFOwnedGLWorker owned_gl_worker;
static DWORD WINAPI owned_gl_worker_run(void*opaque){
 NFOwnedGLWorker*w=opaque;w->consumer=GetCurrentThreadId();HANDLE events[2]={w->stop,w->wake};
 for(;;){DWORD event=WaitForMultipleObjects(2,events,FALSE,INFINITE);if(event==WAIT_OBJECT_0)break;if(event!=WAIT_OBJECT_0+1)return 19;
  w->result=19;NFPresentationSubmission*s=nf_handoff_pop(w->queue);
  if(s){if(w->consumer!=w->producer&&wglMakeCurrent(preview_dc,preview_context)){
   w->result=render_owned_submission(s,w->args);
   if(!w->result){glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,w->pixels);if(glGetError()!=GL_NO_ERROR)w->result=19;}
   glFinish();if(!wglMakeCurrent(NULL,NULL))w->result=19;
  }nf_submission_destroy(s);}
  w->draws++;SetEvent(w->done);
 }
 return 0;
}
/* Producer calls only after final acknowledged draw; join precedes cleanup. */
static int owned_gl_worker_stop(void){
 NFOwnedGLWorker*w=&owned_gl_worker;int ok=1;
 if(w->thread){nf_handoff_close(w->queue);SetEvent(w->stop);ok=WaitForSingleObject(w->thread,INFINITE)==WAIT_OBJECT_0;DWORD code=19;if(!GetExitCodeThread(w->thread,&code)||code)ok=0;CloseHandle(w->thread);w->thread=NULL;w->joins++;}
 nf_handoff_destroy(w->queue);w->queue=NULL;
 if(w->wake)CloseHandle(w->wake);if(w->done)CloseHandle(w->done);if(w->stop)CloseHandle(w->stop);w->wake=w->done=w->stop=NULL;
 if(w->starts)printf("owned_gl_worker_starts=%u owned_gl_worker_joins=%u owned_gl_worker_total_draws=%u\n",w->starts,w->joins,w->draws);
 return ok;
}
static int owned_gl_worker_start(uint64_t epoch){
 NFOwnedGLWorker*w=&owned_gl_worker;if(w->thread)return nf_handoff_epoch(w->queue,epoch);
 w->producer=GetCurrentThreadId();w->queue=nf_handoff_create(epoch);w->wake=CreateEvent(NULL,FALSE,FALSE,NULL);w->done=CreateEvent(NULL,FALSE,FALSE,NULL);w->stop=CreateEvent(NULL,TRUE,FALSE,NULL);
 if(!w->queue||!w->wake||!w->done||!w->stop){owned_gl_worker_stop();return 0;}
 w->thread=CreateThread(NULL,0,owned_gl_worker_run,w,0,NULL);if(!w->thread){owned_gl_worker_stop();return 0;}w->starts++;return 1;
}
static int owned_gl_worker_draw(NFPresentationSubmission*s,char**args,uint8_t*pixels){
 NFOwnedGLWorker*w=&owned_gl_worker;if(!owned_gl_worker_start(nf_submission_time(s)->epoch))return 19;
 NFPresentationSubmission*copy=nf_submission_clone(s);if(!copy||!nf_handoff_push(w->queue,&copy)){nf_submission_destroy(copy);return 19;}
 if(!wglMakeCurrent(NULL,NULL))return 19;
 w->args=args;w->pixels=pixels;w->result=19;SetEvent(w->wake);
 HANDLE events[2]={w->done,w->thread};int completed=WaitForMultipleObjects(2,events,FALSE,INFINITE)==WAIT_OBJECT_0;
 int restored=wglMakeCurrent(preview_dc,preview_context)!=0;
 if(completed&&!w->result&&restored)printf("owned_gl_worker_draw=1 producer=%lu consumer=%lu\n",(unsigned long)w->producer,(unsigned long)w->consumer);
 return completed&&restored?w->result:19;
}
