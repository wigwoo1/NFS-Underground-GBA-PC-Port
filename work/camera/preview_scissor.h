#ifndef NF_PREVIEW_SCISSOR_H
#define NF_PREVIEW_SCISSOR_H
/* Intersect lighting runs with an already enabled surface clip, then restore. */
typedef struct {GLboolean enabled;GLint box[4];} PreviewScissor;
static PreviewScissor preview_scissor_save(void){PreviewScissor s;s.enabled=glIsEnabled(GL_SCISSOR_TEST);glGetIntegerv(GL_SCISSOR_BOX,s.box);return s;}
static void preview_scissor_run(const PreviewScissor*s,int x,int width){
 int left=x,right=x+width,bottom=0,top=2160;
 if(s->enabled){if(left<s->box[0])left=s->box[0];if(right>s->box[0]+s->box[2])right=s->box[0]+s->box[2];if(bottom<s->box[1])bottom=s->box[1];if(top>s->box[1]+s->box[3])top=s->box[1]+s->box[3];}
 glEnable(GL_SCISSOR_TEST);glScissor(left,bottom,right>left?right-left:0,top>bottom?top-bottom:0);
}
static void preview_scissor_restore(const PreviewScissor*s){glScissor(s->box[0],s->box[1],s->box[2],s->box[3]);if(s->enabled)glEnable(GL_SCISSOR_TEST);else glDisable(GL_SCISSOR_TEST);}
#endif
