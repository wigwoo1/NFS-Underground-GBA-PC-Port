#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "preview_resources.h"
#include "preview_scissor.h"
static int box(int x,int y,int w,int h){GLint b[4];glGetIntegerv(GL_SCISSOR_BOX,b);return b[0]==x&&b[1]==y&&b[2]==w&&b[3]==h;}
int main(void){
 if(preview_context_open())return 1;
 glDisable(GL_SCISSOR_TEST);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
 glEnable(GL_SCISSOR_TEST);glScissor(10,12,20,18);PreviewScissor s=preview_scissor_save();
 preview_scissor_run(&s,20,20);if(!box(20,12,10,18))return 2;
 glClearColor(1,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
 unsigned char pixels[40*40*3];glReadPixels(0,0,40,40,GL_RGB,GL_UNSIGNED_BYTE,pixels);
 for(int y=0;y<40;y++)for(int x=0;x<40;x++){unsigned char*p=pixels+(y*40+x)*3;int inside=x>=20&&x<30&&y>=12&&y<30;if(p[0]!=(inside?255:0)||p[1]||p[2])return 3;}
 preview_scissor_run(&s,35,5);if(!box(35,12,0,18))return 4;
 preview_scissor_restore(&s);if(!glIsEnabled(GL_SCISSOR_TEST)||!box(10,12,20,18))return 5;
 glDisable(GL_SCISSOR_TEST);s=preview_scissor_save();preview_scissor_run(&s,300,27);if(!box(300,0,27,2160))return 6;
 preview_scissor_restore(&s);if(glIsEnabled(GL_SCISSOR_TEST)||!box(10,12,20,18)||glGetError())return 7;
 puts("{\"result\":\"PASS\",\"pixel_checks\":1600,\"scope\":\"Lighting scissor intersection, empty intersection and GL state restoration\"}");preview_shutdown();return 0;
}
